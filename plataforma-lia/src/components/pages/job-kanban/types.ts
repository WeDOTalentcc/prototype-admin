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
  chips?: string[]
  flagFavorite?: boolean
  flagNotes?: boolean
  flagStaleTooltip?: string
  flagHighScoreTooltip?: string
  flagLowScoreTooltip?: string
  flagAttention?: { tooltip: string }
  dateLabel?: string
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
