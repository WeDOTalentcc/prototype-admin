export interface TableCandidate {
  id: string
  name: string
  email?: string
  phone?: string
  avatar?: string
  avatar_url?: string
  position?: string
  current_title?: string
  current_company?: string
  location?: string
  location_city?: string
  location_state?: string
  workModel?: 'remoto' | 'híbrido' | 'presencial'
  work_model_preference?: string
  score?: number
  lia_score?: number
  skills?: string[]
  technical_skills?: string[]
  experience?: number
  years_of_experience?: number
  linkedin?: string
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  source?: string
  stage?: string
  status?: string
  sub_status?: string
  tags?: string[]
  salary?: {
    current: number
    expected: number
  }
  current_salary?: number
  desired_salary_max?: number
  contractType?: 'CLT' | 'PJ' | 'Freelancer'
  contract_type_preference?: string
  liaAnalysis?: {
    score: number
    strengths: string[]
    concerns: string[]
    recommendation: string
  }
  bigFive?: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  }
  workHistory?: Array<{
    company: string
    position?: string
    title?: string
    period?: string
    description?: string
  }>
  has_email?: boolean
  has_phone?: boolean
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  timezone?: string
  company_hq?: string
  funding_stage?: string
  institution_tier?: string
  company_industries?: string[]
  company_size?: string
  [key: string]: unknown
}

export interface TableColumn {
  id: string
  label: string
  visible?: boolean
  sortable?: boolean
  width?: number | string
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  category?: string
  order?: number
  isGlobalSearch?: boolean
  render?: (candidate: TableCandidate, column: TableColumn) => React.ReactNode
}

export interface TableSortConfig {
  field: string
  direction: 'asc' | 'desc'
}

export interface UnifiedTableProps {
  candidates: TableCandidate[]
  columns: TableColumn[]
  selectedIds?: Set<string>
  pinnedIds?: Set<string>
  favoriteIds?: Set<string>
  sortConfig?: TableSortConfig
  isLoading?: boolean
  emptyMessage?: string
  showCheckboxes?: boolean
  showPagination?: boolean
  pageSize?: number
  enableVirtualScroll?: boolean
  enableColumnResize?: boolean
  enableColumnReorder?: boolean
  jobVacancyId?: string
  isInteractive?: boolean
  onColumnResize?: (columnId: string, width: number) => void
  onColumnReorder?: (columns: TableColumn[]) => void
  onCandidateClick?: (candidate: TableCandidate) => void
  onSelectionChange?: (selectedIds: Set<string>) => void
  onSortChange?: (config: TableSortConfig) => void
  onTogglePin?: (candidateId: string) => void
  onToggleFavorite?: (candidateId: string, note?: string) => void
  onStatusChange?: (candidateId: string, newSubStatus: string, stage: string, jobVacancyId?: string) => Promise<boolean>
  onStageChange?: (candidateId: string, newStage: string, subStatus?: string, jobVacancyId?: string) => Promise<boolean>
  onTransitionRequest?: (candidate: {
    id: string
    name: string
    email?: string
    phone?: string
    avatar?: string
    currentTitle?: string
  }, fromStage: string, toStage: string) => void
  renderActions?: (candidate: TableCandidate) => React.ReactNode
  renderLeftOverlayActions?: (candidate: TableCandidate) => React.ReactNode
  renderCustomCell?: (candidate: TableCandidate, columnId: string) => React.ReactNode | null
  renderCustomHeader?: (columnId: string, defaultLabel: string) => React.ReactNode | null
  getStageBorderColor?: (candidate: TableCandidate) => string | undefined
  getNeedsAction?: (candidate: TableCandidate) => boolean
  className?: string
}

export interface CandidateRowProps {
  candidate: TableCandidate
  columns: TableColumn[]
  isSelected?: boolean
  isPinned?: boolean
  isFavorite?: boolean
  showCheckbox?: boolean
  needsAction?: boolean
  stageBorderColor?: string
  jobVacancyId?: string
  isInteractive?: boolean
  onRowClick?: () => void
  onToggleSelect?: () => void
  onTogglePin?: () => void
  onToggleFavorite?: () => void
  onStatusChange?: (candidateId: string, newSubStatus: string, stage: string, jobVacancyId?: string) => Promise<boolean>
  onStageChange?: (candidateId: string, newStage: string, subStatus?: string, jobVacancyId?: string) => Promise<boolean>
  onTransitionRequest?: (candidate: {
    id: string
    name: string
    email?: string
    phone?: string
    avatar?: string
    currentTitle?: string
  }, fromStage: string, toStage: string) => void
  renderActions?: () => React.ReactNode
  renderLeftOverlayActions?: () => React.ReactNode
  renderCustomCell?: (columnId: string) => React.ReactNode | null
  style?: React.CSSProperties
}
