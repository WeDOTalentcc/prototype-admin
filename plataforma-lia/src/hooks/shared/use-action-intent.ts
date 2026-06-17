"use client"

/**
 * useActionIntent — Detecta intenção de ação a partir da mensagem do usuário.
 *
 * Classifica localmente (sem LLM) se a mensagem indica:
 *   - "wizard"     → criação de nova vaga / headcount
 *   - "wsi"        → entrevista WSI / avaliação de candidato
 *   - null         → conversa geral
 *
 * Threshold de confiança: 0.70 — abaixo disso, retorna null (geral).
 *
 * Compatível com Vue/Nuxt: mapeia para composable useActionIntent().
 */

import { useCallback } from "react"

export type ActionType = "wizard" | "wsi" | "analytics" | "communication" | "ats_integration" | "task_reminder" | "note" | "calendar" | "candidate_field" | "studio_create" | "studio_query" | "studio_metrics" | null

export interface ActionIntentResult {
  actionType: ActionType
  confidence: number
  /** Texto de contexto a mostrar no banner do float ("Modo: Criação de Vaga") */
  label: string | null
}

const ACTION_CONFIDENCE_THRESHOLD = 0.70

// ─── Padrões de intenção ───────────────────────────────────────────────────────

const WIZARD_KEYWORDS = [
  "criar vaga", "nova vaga", "abrir vaga", "cadastrar vaga",
  "novo headcount", "headcount", "job description",
  "preciso contratar", "quero contratar", "vou contratar",
  "abrir processo seletivo", "novo processo seletivo",
  "criar posição", "nova posição", "posição aberta",
  "requisição de vaga", "requisitar vaga",
]

const WSI_KEYWORDS = [
  "entrevistar", "entrevista", "iniciar entrevista", "começar entrevista",
  "avaliar candidato", "avaliação wsi", "wsi", "assessment",
  "triagem de candidato", "triagem por voz", "chamada de triagem",
  "aplicar wsi", "fazer wsi", "rodar wsi",
  "score do candidato", "pontuar candidato",
]

const ANALYTICS_KEYWORDS = [
  "relatório", "relatorio", "gerar relatório", "relatório de vagas",
  "indicadores", "kpi", "kpis", "métricas", "metricas",
  "dashboard de analytics", "analytics", "análise de dados",
  "tempo médio de contratação", "time to hire", "taxa de conversão",
  "previsão de contratação", "predição", "benchmarking",
  "performance do funil", "desempenho do processo",
]

const COMMUNICATION_KEYWORDS = [
  "enviar email", "mandar email", "email para candidato",
  "notificar candidato", "notificação", "mensagem para candidato",
  "enviar whatsapp", "mensagem whatsapp", "contato com candidato",
  "comunicar candidato", "aviso de processo", "feedback ao candidato",
  "enviar feedback", "comunicação em massa", "disparo de mensagens",
]

const ATS_KEYWORDS = [
  "sincronizar", "sincronizar gupy", "sincronizar pandapé", "sincronizar pandape",
  "importar candidatos", "importar vagas", "importar do ats",
  "exportar para ats", "integração ats", "gupy", "pandapé", "pandape",
  "merge ats", "conectar ats", "atualizar ats", "sync ats",
  "candidatos do ats", "vagas do ats",
]

const TASK_REMINDER_KEYWORDS = [
  "me lembra", "me avisa", "lembrete", "criar lembrete", "cria um lembrete",
  "criar tarefa", "cria uma tarefa", "nova tarefa", "adicionar tarefa",
  "to do", "to-do", "lista de tarefas", "tarefa para",
  "me lembra de", "não esquece", "não me deixa esquecer",
]

const NOTE_KEYWORDS = [
  "anota", "anotar", "anote", "salva uma nota", "registra", "cria uma nota",
  "nota sobre", "nota para", "anotação", "salvar observação",
  "registrar observação", "observação sobre", "adicionar nota",
  "quero registrar", "quero anotar",
]

const CALENDAR_KEYWORDS = [
  "criar compromisso", "novo compromisso", "agendar reunião", "agendar call",
  "agendar alinhamento", "criar evento", "compromisso no calendário",
  "reunião no calendário", "marcar reunião", "nova reunião",
  "minha agenda", "agenda de hoje", "resumo da agenda", "o que tenho hoje",
  "compromissos de hoje",
]

const CANDIDATE_FIELD_KEYWORDS = [
  "atualiza o email", "atualiza o telefone", "atualiza o celular",
  "atualiza o linkedin", "atualiza o cargo", "atualiza a empresa",
  "atualiza a cidade", "atualiza o estado", "atualiza o salário",
  "muda o email", "muda o telefone", "muda o celular",
  "muda o linkedin", "muda o cargo", "muda a empresa",
  "troca o email", "troca o telefone", "troca o celular",
  "atualizar campo", "atualizar cadastro do candidato",
]

// ─── Scoring ──────────────────────────────────────────────────────────────────

function scoreKeywords(message: string, keywords: string[]): number {
  const lower = message.toLowerCase()
  let hits = 0
  for (const kw of keywords) {
    if (lower.includes(kw)) hits++
  }
  return hits
}

const STUDIO_CREATE_KEYWORDS = [
  "criar agente", "criar agent", "novo agente", "novo agent",
  "cria um agente", "cria um agent", "configura um agente", "configure um agent",
  "montar agente", "montar agent", "quero um agente", "quero um agent",
  "agente de triagem", "agent de triagem", "agente que filtra", "agent que filtra",
  "agente para sourcing", "agent para sourcing", "agente de comunicacao", "agente de comunicação",
  "studio agent", "agent studio", "criar assistente", "novo assistente",
]

const STUDIO_QUERY_KEYWORDS = [
  "como esta o agente", "como está o agente", "como esta o agent", "como está o agent",
  "status do agente", "status do agent", "detalhes do agente", "detalhes do agent",
  "me fala sobre o agente", "me fala sobre o agent", "info do agente", "info do agent",
  "qual a configuracao do agente", "qual a configuração do agent",
  "ver agente", "ver agent", "mostrar agente", "mostrar agent",
  "o agente", "o agent",
]

const STUDIO_METRICS_KEYWORDS = [
  "consumo dos agentes", "consumo dos agents", "meu consumo",
  "quantas execucoes", "quantas execuções", "execucoes hoje", "execuções hoje",
  "execucoes essa semana", "execuções essa semana", "execucoes do mes", "execuções do mês",
  "qual agente mais rodou", "qual agent mais rodou", "top agentes", "top agents",
  "metricas dos agentes", "métricas dos agentes", "metricas do studio", "métricas do studio",
  "custo dos agentes", "custo dos agents", "tokens consumidos",
  "dashboard dos agentes", "dashboard dos agents",
]

interface ScoredAction {
  actionType: NonNullable<ActionType>
  score: number
  confidence: number
  label: string
}

function detectActionType(message: string): ActionIntentResult {
  if (!message.trim()) {
    return { actionType: null, confidence: 0, label: null }
  }

  const candidates: ScoredAction[] = [
    {
      actionType: "wsi",
      score: scoreKeywords(message, WSI_KEYWORDS),
      confidence: 0,
      label: "Modo: Entrevista WSI",
    },
    {
      actionType: "wizard",
      score: scoreKeywords(message, WIZARD_KEYWORDS),
      confidence: 0,
      label: "Modo: Criação de Vaga",
    },
    {
      actionType: "analytics",
      score: scoreKeywords(message, ANALYTICS_KEYWORDS),
      confidence: 0,
      label: "Modo: Analytics & Relatórios",
    },
    {
      actionType: "communication",
      score: scoreKeywords(message, COMMUNICATION_KEYWORDS),
      confidence: 0,
      label: "Modo: Comunicação com Candidatos",
    },
    {
      actionType: "ats_integration",
      score: scoreKeywords(message, ATS_KEYWORDS),
      confidence: 0,
      label: "Modo: Integração ATS",
    },
    {
      actionType: "task_reminder",
      score: scoreKeywords(message, TASK_REMINDER_KEYWORDS),
      confidence: 0,
      label: "Modo: Tarefas & Lembretes",
    },
    {
      actionType: "note",
      score: scoreKeywords(message, NOTE_KEYWORDS),
      confidence: 0,
      label: "Modo: Anotações",
    },
    {
      actionType: "calendar",
      score: scoreKeywords(message, CALENDAR_KEYWORDS),
      confidence: 0,
      label: "Modo: Agenda & Compromissos",
    },
    {
      actionType: "candidate_field",
      score: scoreKeywords(message, CANDIDATE_FIELD_KEYWORDS),
      confidence: 0,
      label: "Modo: Atualizar Candidato",
    },
    {
      actionType: "studio_create",
      score: scoreKeywords(message, STUDIO_CREATE_KEYWORDS),
      confidence: 0,
      label: "Modo: Criar Agent Studio",
    },
    {
      actionType: "studio_query",
      score: scoreKeywords(message, STUDIO_QUERY_KEYWORDS),
      confidence: 0,
      label: "Modo: Consultar Agent",
    },
    {
      actionType: "studio_metrics",
      score: scoreKeywords(message, STUDIO_METRICS_KEYWORDS),
      confidence: 0,
      label: "Modo: Metricas Studio",
    },
  ]

  // Calcular confidence para cada candidato
  for (const c of candidates) {
    c.confidence = Math.min(0.95, 0.65 + c.score * 0.10)
  }

  // Selecionar o de maior score (com ties desfeitos pela ordem acima)
  const best = candidates.reduce((a, b) => b.score > a.score ? b : a)

  if (best.score > 0 && best.confidence >= ACTION_CONFIDENCE_THRESHOLD) {
    return {
      actionType: best.actionType,
      confidence: best.confidence,
      label: best.label,
    }
  }

  return { actionType: null, confidence: best.confidence, label: null }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export interface UseActionIntentResult {
  detect: (message: string) => ActionIntentResult
}

export function useActionIntent(): UseActionIntentResult {
  const detect = useCallback((message: string): ActionIntentResult => {
    return detectActionType(message)
  }, [])

  return { detect }
}

/** Mapeia ActionType para o domain string que o WebSocket backend espera. */
export function actionTypeToDomain(actionType: ActionType): string {
  switch (actionType) {
    case "wizard":          return "wizard"
    case "wsi":             return "talent"
    case "analytics":       return "analytics"
    case "communication":   return "communication"
    case "ats_integration": return "ats_integration"
    case "task_reminder":   return "task_planning"
    case "note":            return "task_planning"
    case "calendar":        return "interview_scheduling"
    case "candidate_field": return "pipeline_action"
    case "studio_create":   return "agent_studio"
    case "studio_query":    return "agent_studio"
    case "studio_metrics":  return "agent_studio"
    default:                return "general"
  }
}
