import {
  Search,
  ClipboardList,
  FileText,
  CheckCircle,
  UserCheck,
  MonitorPlay,
  Languages,
  Code,
  Handshake,
  Phone,
  FileCheck,
  Award,
  GitBranch,
  UserCog,
  ShieldCheck,
  HeartPulse,
  Presentation,
  BookOpen,
  Megaphone,
  type LucideIcon,
  CircleDot,
  Layers,
  Clipboard,
  Star,
  Briefcase,
  ListChecks,
  MessageSquare,
  ThumbsUp,
  XCircle,
  Clock,
  Filter,
} from "lucide-react"

export const STAGE_ICON_MAP: Record<string, LucideIcon> = {
  sourcing: Search,
  screening: ClipboardList,
  long_list: FileText,
  short_list: CheckCircle,
  interview_hr: UserCheck,
  technical_test: MonitorPlay,
  english_test: Languages,
  interview_technical: Code,
  interview_manager: Handshake,
  interview_final: Presentation,
  reference_check: Phone,
  offer: FileCheck,
  hired: Award,
  contratado: Award,
  rejected: XCircle,
  recusado: XCircle,
  offer_declined: XCircle,
  background_check: ShieldCheck,
  medical_exam: HeartPulse,
  onboarding: BookOpen,
  talent_pool: Layers,
  pre_screening: Filter,
  cultural_fit: Star,
  case_study: Clipboard,
  group_dynamics: Megaphone,
  salary_negotiation: Briefcase,
  documentation: ListChecks,
  feedback: MessageSquare,
  approval: ThumbsUp,
  waiting: Clock,
  assessment: MonitorPlay,
  evaluation: UserCog,
}

const BEHAVIOR_ICON_MAP: Record<string, LucideIcon> = {
  gate: ShieldCheck,
  schedule: Handshake,
  evaluate: MonitorPlay,
  notify: Megaphone,
  passive: CircleDot,
  collect: Clipboard,
  approve: ThumbsUp,
  reject: XCircle,
}

const CATEGORY_ICON_MAP: Record<string, LucideIcon> = {
  sourcing: Search,
  screening: ClipboardList,
  interview: UserCheck,
  evaluation: MonitorPlay,
  offer: FileCheck,
  final: Award,
  rejection: XCircle,
  other: GitBranch,
}

const ICON_POOL: LucideIcon[] = [
  CircleDot, Layers, Clipboard, Star, Briefcase,
  ListChecks, MessageSquare, ThumbsUp, BookOpen,
  ShieldCheck, HeartPulse, Presentation, Filter,
]

export function getStageIcon(
  stageName: string,
  actionBehavior?: string,
  stageCategory?: string
): LucideIcon {
  const key = stageName.toLowerCase().replace(/\s+/g, "_")

  if (STAGE_ICON_MAP[key]) return STAGE_ICON_MAP[key]

  if (actionBehavior && BEHAVIOR_ICON_MAP[actionBehavior]) {
    return BEHAVIOR_ICON_MAP[actionBehavior]
  }

  if (stageCategory && CATEGORY_ICON_MAP[stageCategory]) {
    return CATEGORY_ICON_MAP[stageCategory]
  }

  let hash = 0
  for (let i = 0; i < key.length; i++) {
    hash = ((hash << 5) - hash) + key.charCodeAt(i)
    hash = hash & hash
  }
  return ICON_POOL[Math.abs(hash) % ICON_POOL.length]
}

export const STAGE_VIBRANT_COLORS: Record<string, string> = {
  sourcing: "#5DA47A",
  screening: "#5DA47A",
  long_list: "#60BED1",
  short_list: "#60BED1",
  pre_screening: "#5DA47A",
  interview_hr: "#D19960",
  technical_test: "#D17060",
  english_test: "#D1A960",
  interview_technical: "#9860D1",
  interview_manager: "#9860D1",
  interview_final: "#8B5CF6",
  reference_check: "#D19960",
  background_check: "#6078D1",
  medical_exam: "#60BED1",
  offer: "#6078D1",
  proposal: "#6078D1",
  proposta: "#6078D1",
  salary_negotiation: "#6078D1",
  hired: "#5DA47A",
  contratado: "#5DA47A",
  onboarding: "#5DA47A",
  rejected: "#8A8F98",
  recusado: "#8A8F98",
  offer_declined: "#8A8F98",
  talent_pool: "#60BED1",
  cultural_fit: "#D1A960",
  case_study: "#D17060",
  group_dynamics: "#9860D1",
  assessment: "#D17060",
  evaluation: "#D19960",
  documentation: "#6078D1",
  feedback: "#D19960",
  approval: "#5DA47A",
  waiting: "#8A8F98",
}

const COLOR_PALETTE = [
  "#5DA47A", "#60BED1", "#D19960", "#D17060",
  "#9860D1", "#6078D1", "#D1A960", "#8B5CF6",
  "#4DA6A0", "#C96B8A", "#7B8FD1", "#D18B60",
]

export function getStageColor(stageName: string, fallbackHex?: string): string {
  const key = stageName.toLowerCase().replace(/\s+/g, "_")
  if (STAGE_VIBRANT_COLORS[key]) return STAGE_VIBRANT_COLORS[key]
  if (fallbackHex && fallbackHex !== "#6366f1" && fallbackHex !== "#2D2D2D") return fallbackHex

  let hash = 0
  for (let i = 0; i < key.length; i++) {
    hash = ((hash << 5) - hash) + key.charCodeAt(i)
    hash = hash & hash
  }
  return COLOR_PALETTE[Math.abs(hash) % COLOR_PALETTE.length]
}

export const INTERNAL_STAGE_NAMES = new Set([
  "initial",
  "pending_gate1",
  "pending_gate2",
  "new",
  "novo",
  "triagem",
  "entrevista rh",
  "entrevista técnica",
  "entrevista final",
  "proposta",
])

export const STATUS_TRANSLATION_MAP: Record<string, string> = {
  active: "Ativo",
  inactive: "Inativo",
  hired: "Contratado",
  rejected: "Reprovado",
  novo: "Novo",
  sourced: "Prospectado",
  screening: "Em Triagem",
  interview: "Em Entrevista",
  offer: "Proposta",
  withdrawn: "Desistiu",
  on_hold: "Em Espera",
  pending: "Pendente",
  approved: "Aprovado",
  declined: "Recusado",
  new: "Novo",
  triado: "Triado",
  triado_aprovado: "Triado - Aprovado",
  awaiting_screening: "Aguardando Triagem",
  cv_pending_review: "Revisão Manual Pendente",
}

export function translateStatus(rawStatus: string): string {
  if (!rawStatus) return "Não informado"
  const key = rawStatus.toLowerCase().trim()
  return STATUS_TRANSLATION_MAP[key] || rawStatus
}
