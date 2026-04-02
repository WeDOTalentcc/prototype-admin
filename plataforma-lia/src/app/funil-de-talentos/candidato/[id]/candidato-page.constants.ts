// candidato-page.constants.ts
// Pure static data: tab labels, status maps, category configs

import type { NoteCategory } from "./candidato-page.types"

export const CANDIDATE_STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; border: string }> = {
  active:     { label: "Ativo",         bg: "bg-status-success/10",           text: "text-status-success", border: "border-status-success/30" },
  do_not_use: { label: "Não Utilizar",  bg: "bg-status-error/10",             text: "text-status-error",   border: "border-status-error/30" },
  hired:      { label: "Contratado",    bg: "bg-lia-bg-secondary dark:bg-lia-bg-primary", text: "text-lia-text-primary dark:text-lia-text-primary", border: "border-lia-border-default dark:border-lia-border-default" },
  inactive:   { label: "Inativo",       bg: "bg-lia-bg-tertiary",                    text: "text-lia-text-secondary",        border: "border-lia-border-default" },
}

export const NOTE_CATEGORY_OPTIONS: Array<{ value: NoteCategory; label: string }> = [
  { value: "general",   label: "📋 Nota Geral" },
  { value: "interview", label: "🎤 Nota de Entrevista" },
  { value: "screening", label: "📞 Nota de Triagem" },
  { value: "feedback",  label: "💬 Feedback Interno" },
  { value: "technical", label: "💻 Avaliação Técnica" },
]

export const NOTE_CATEGORY_LABELS: Record<string, string> = {
  general:   "Geral",
  interview: "Entrevista",
  screening: "Triagem",
  feedback:  "Feedback",
  technical: "Técnica",
}

export const ACTIVITY_FILTER_LABELS: Record<string, string> = {
  all:          "Todas",
  emails:       "📧 Emails",
  interviews:   "🎤 Entrevistas",
  tests:        "📝 Testes",
  lia:          "🤖 LIA",
  offers:       "💼 Ofertas",
  applications: "📋 Inscrições",
  notes:        "📝 Notas",
}

export const PERIOD_FILTER_OPTIONS = [
  { value: "7days",    label: "Últimos 7 dias" },
  { value: "30days",   label: "Últimos 30 dias" },
  { value: "3months",  label: "Últimos 3 meses" },
  { value: "all",      label: "Todo período" },
] as const

export const ANALYSIS_TYPE_LABELS: Record<string, string> = {
  bullet_points:    "Pontos-chave",
  short_paragraph:  "Resumo",
  detailed_bullets: "Análise Detalhada",
}

export const ACCEPTED_FILE_TYPES = ".pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov"
export const MAX_FILE_SIZE_LABEL = "PDF, DOC, DOCX, JPG, PNG, MP4 • Máx 10MB"
