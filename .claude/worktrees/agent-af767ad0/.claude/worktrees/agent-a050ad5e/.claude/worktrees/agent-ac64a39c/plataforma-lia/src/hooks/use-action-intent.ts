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

export type ActionType = "wizard" | "wsi" | "analytics" | "communication" | "ats_integration" | null

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

// ─── Scoring ──────────────────────────────────────────────────────────────────

function scoreKeywords(message: string, keywords: string[]): number {
  const lower = message.toLowerCase()
  let hits = 0
  for (const kw of keywords) {
    if (lower.includes(kw)) hits++
  }
  return hits
}

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
    case "wizard":        return "wizard"
    case "wsi":           return "talent"          // WSI usa o TalentReActAgent
    case "analytics":     return "analytics"
    case "communication": return "communication"
    case "ats_integration": return "ats_integration"
    default:              return "general"
  }
}
