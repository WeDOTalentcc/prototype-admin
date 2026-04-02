/**
 * expandable-ai-prompt.types.ts
 * Tipos, interfaces e constantes extraídos do ExpandableAIPrompt (P1-E).
 * Importar daqui em todos os hooks e sub-componentes relacionados.
 */

import type { QuickAction } from "@/components/ui/quick-action-chips"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"

// ── Tipos de navegação ──────────────────────────────────────────────────────

export type SearchTab = 'natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'
export type SearchSource = 'local' | 'global' | 'hybrid'

// ── Entidades e análise ─────────────────────────────────────────────────────

export interface BackendEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

export interface SearchAnalysis {
  completeness_score: number
  criteria_found: { type: string; value: string; label: string }[]
  criteria_missing: { type: string; label: string; importance: string }[]
  alerts: { severity: string; message: string; suggestion?: string; action_value?: string }[]
  suggestions: string[]
  enrichment_suggestions?: Record<string, string[]>
  next_recommended_action?: string
}

export interface SearchCriterion {
  id: string
  type: 'location' | 'job_title' | 'experience' | 'years_experience' | 'industry' | 'skills' | 'seniority' | 'company' | 'education' | 'language'
  label: string
  value: string
  active: boolean
}

export interface AutocompleteSuggestion {
  text: string
  category: string
  icon?: string
  description?: string
  insert_text?: string
}

// ── Arquétipos ──────────────────────────────────────────────────────────────

export interface ArchetypeData {
  id: string
  name: string
  description?: string
  department?: string
  hired_candidate?: { name: string }
  criteria?: Record<string, unknown>
}

// ── Perfis similares ────────────────────────────────────────────────────────

export interface SimilarProfile {
  url: string
  type: 'linkedin' | 'cv'
  filename?: string
}

// ── Props do componente principal ───────────────────────────────────────────

export interface ContextPillData {
  icon: React.ReactNode
  primaryText: string
  secondaryText: string
  onDismiss?: () => void
}

export interface JobContext {
  id?: string
  title?: string
  status?: string
}

export interface ExpandableAIPromptProps {
  selectedCandidates: unknown[]
  onCommand: (command: string, action: string) => void
  filteredCount: number
  totalCount: number
  forceExpanded?: boolean
  candidateContext?: unknown
  onClose?: () => void
  contextPill?: ContextPillData
  quickActions?: QuickAction[]
  jobContext?: JobContext
  pageContext?: 'candidates' | 'jobs'
}

// ── Constantes ──────────────────────────────────────────────────────────────

export const ENTITY_LABELS: Record<string, string> = {
  job_title: 'Cargo',
  location: 'Localização',
  years_experience: 'Experiência',
  industry: 'Setor',
  skills: 'Habilidades',
  seniority: 'Senioridade',
  company: 'Empresa',
}

export const CRITERIA_TYPE_MAP: Record<string, string> = {
  'Cargo': 'job_title',
  'Localização': 'location',
  'Experiência': 'years_experience',
  'Setor': 'industry',
  'Habilidades': 'skills',
  'Habilidade': 'skills',
  'Senioridade': 'seniority',
  'Empresa': 'company',
}

export const MAX_SIMILAR_URLS = 2
export const MAX_CV_FILES = 2

// Nota: CONTEXT_COLORS usa hex hardcoded (débito técnico — migrar para tokens DS v4.2.1 em ciclo futuro)
export const CONTEXT_COLORS: Record<string, {
  border: string
  bg: string
  headerText: string
  headerBg: string
}> = {
  candidates: {
    border: 'var(--wedo-green-light)',
    bg: 'var(--wedo-green-bg-10)',
    headerText: 'var(--status-success)',
    headerBg: 'var(--wedo-green-bg-15)',
  },
  jobs: {
    border: 'var(--lia-text-tertiary)',
    bg: 'var(--lia-bg-secondary)',
    headerText: 'var(--lia-text-secondary)',
    headerBg: 'var(--lia-bg-secondary)',
  },
}

// Re-export para conveniência
export type { SearchFilters, QuickAction }
