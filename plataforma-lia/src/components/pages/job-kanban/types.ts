export interface KanbanCandidate {
  id: string
  candidateId: string
  name: string
  email: string
  avatar_url?: string
  current_title?: string
  current_company?: string
  lia_score?: number
  skills?: string[]
  status: string
  substatus?: string
  stageId: string
  order: number
  addedAt: string
  movedAt?: string
  notes?: string
  tags?: string[]
  days_in_stage?: number
  lia_insights?: {
    strengths?: string[]
    concerns?: string[]
    recommendation?: string
  }
}

export interface KanbanStage {
  id: string
  name: string
  color: string
  order: number
  isDefault?: boolean
  candidates: KanbanCandidate[]
  candidateCount: number
  substatuses?: SubStatus[]
}

export interface SubStatus {
  id: string
  label: string
  color: string
  isDefault?: boolean
}

export interface KanbanJob {
  id: string
  title: string
  department?: string
  location?: string
  status: 'draft' | 'active' | 'paused' | 'closed'
  stages: KanbanStage[]
  totalCandidates: number
  createdAt: string
}

export interface MoveAction {
  candidateId: string
  fromStageId: string
  toStageId: string
  newSubstatus?: string
  reason?: string
}

export interface LIASuggestion {
  type: 'substatus' | 'next_action' | 'feedback'
  content: string
  confidence: number
  metadata?: Record<string, unknown>
}

export interface KanbanPageState {
  job: KanbanJob | null
  selectedCandidate: KanbanCandidate | null
  isLoading: boolean
  isMoveModalOpen: boolean
  pendingMove: MoveAction | null
  liaSuggestions: LIASuggestion[]
}

export interface KanbanItem {
  id: string
  title: string
  subtitle?: string
  tertiary?: string
  avatarUrl?: string
  avatarFallback?: string
  score?: number
  scoreColorClass?: string
  badge?: string
  /**
   * Task #562 — Chips podem ser strings simples (compat) OU objetos com
   * ícone semântico (`briefcase` para work model, `star` para senioridade,
   * `users` para contagem de candidatos). O card resolve o componente
   * Lucide a partir do nome.
   */
  chips?: Array<string | { icon?: "briefcase" | "users" | "star"; label: string }>

  flagFavorite?: boolean
  flagNotes?: boolean
  flagStaleTooltip?: string
  flagHighScoreTooltip?: string
  flagLowScoreTooltip?: string
  flagAttention?: { tooltip: string }
  dateLabel?: string
  /** Optional progress 0..100 — when present, renders a progress bar on the card */
  progressPercent?: number
  /**
   * Task #562 — Mini funil horizontal por estágio. Quando ausente OU sem
   * `total > 0`, o card cai para a barra de progresso simples (sem default
   * silencioso — o mapper não inventa números). Estágios refletem o shape
   * canônico de `JobFunnel` (lib/jobs/funnel).
   */
  funnel?: {
    total: number
    screening: number
    interview: number
    final: number
    hired: number
  }
  /**
   * Task #562 — Ribbon superior alinhado ao card de candidato. Disparado
   * pelo mapper quando a vaga está em estado de atenção (urgência alta,
   * deadline vencido ou prioridade alta). Renderizado via slot `ribbon`
   * de `KanbanCardShell` para reuso visual.
   */
  ribbon?: {
    label: string
    variant: "warning" | "danger" | "info"
    /**
     * Task #562 — Motivo acionável (renderizado no tooltip e como subline).
     * Obrigatório para que o ribbon seja útil ao recrutador (decisão do
     * code review: ribbons sem reason violam a expectativa de ação).
     */
    reason: string
  }
  /**
   * Task #562 — Owner/responsável da vaga (manager). Backend devolve
   * string simples; sem FK. Quando ausente, o card omite a linha — não
   * renderiza placeholder.
   */
  owner?: {
    name: string
    initials: string
    avatarUrl?: string
  }
  /** Task #562 — Idade da vaga em dias (desde openDate). */
  ageDays?: number
  /**
   * Task #592 — Status informativo de campanha (LIA executando a vaga).
   * Quando ausente, o card busca via JobCampaignBadge usando o `id`. Quando
   * presente, força o estado (útil para testes / Storybook).
   */
  campaignStatus?: "active" | "paused" | "none"
  /**
   * Task #562 — Status do deadline para colorir o chip:
   *  - `ok`: > 7 dias restantes
   *  - `warning`: ≤ 7 dias restantes
   *  - `danger`: vencido (negativo)
   */
  deadlineStatus?: "ok" | "warning" | "danger"
}

export interface DragResult {
  draggableId: string
  source: {
    droppableId: string
    index: number
  }
  destination: {
    droppableId: string
    index: number
  } | null
}
