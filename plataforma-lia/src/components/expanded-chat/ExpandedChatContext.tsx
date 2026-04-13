'use client'


import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { createContext, useContext, ReactNode } from 'react'
import { type WizardStage } from './config'
import type { FastTrackJobData } from '@/hooks/recruitment/useFastTrack'

export interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool' | 'general'
  weight: number
  weightJustification?: string
  isWeightInferred?: boolean
}

export interface BehavioralCompetency {
  id: string
  name: string
  weight: number
  justification: string
  enabled: boolean
  weightJustification?: string
  isWeightInferred?: boolean
}

export interface Benefit {
  id: string
  name: string
  value?: string
  enabled: boolean
}

export interface SalaryInfo {
  minSalary: string
  maxSalary: string
  minBonus: string
  maxBonus: string
  bonusCriteria: string
  benefits: Benefit[]
}

export interface WSIQuestion {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean
  options?: string[]
  expectedAnswer?: string | number | boolean
  correctOptionIndex?: number
  competencyValidated?: string
}

export interface DetectedCriteria {
  cargo: string | null
  gestorArea: string | null
  responsabilidades: string[]
  competenciasTecnicas: string[]
  competenciasComportamentais: string[]
  idiomas: string[]
  senioridadeIdiomas: string | null
  modeloTrabalho: string | null
  localizacao: string | null
  tipoContrato: string | null
  salario: string | null
  departamento: string | null
  isAffirmative: boolean | null
  affirmativeCriteriaPrimary: string | null
  affirmativeCriteriaSecondary: string | null
  affirmativeDescription: string | null
  experienciaMinima: string | null
  formacao: string[]
  certificacoes: string[]
  ferramentas: string[]
  diasPresenciais: number | null
  beneficiosMencionados: string[]
  bonus: string | null
  viagensFrequentes: boolean | null
  disponibilidade: string | null
  cnh: string | null
  horario: string | null
}

export interface BasicInfoFields {
  cargo: string
  area: string
  gestor: string
  localidade: string
  modeloTrabalho: string
  tipoContrato: string
}

export type CatalogMaturity = 'complete' | 'partial' | 'minimal'

export interface WizardContextState {
  currentStage: WizardStage
  currentStageIndex: number
  wizardDraftId: string
  basicInfoFields: BasicInfoFields
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  salaryInfo: SalaryInfo
  wsiQuestions: WSIQuestion[]
  detectedCriteria: DetectedCriteria
  generatedJobDescription: string
  hasRestoredDraft: boolean
  hasPendingChanges: boolean
  catalogMaturity: CatalogMaturity
  isLoading: boolean
  wsiQualityNota: number
  wsiMissingFields: string[]
  fastTrackSourceJobId: string | null
}

export interface OrchestratorFieldUpdates {
  salaryInfo?: Partial<SalaryInfo>
  basicInfoFields?: Partial<BasicInfoFields>
  technicalSkills?: TechnicalSkill[]
  behavioralCompetencies?: BehavioralCompetency[]
  detectedCriteria?: Partial<DetectedCriteria>
}

export interface WizardContextActions {
  setCurrentStage: (stage: WizardStage) => void
  advanceStage: () => void
  goBackStage: () => void
  updateBasicInfoField: (field: keyof BasicInfoFields, value: string) => void
  updateBasicInfoFields: (fields: Partial<BasicInfoFields>) => void
  updateSalaryInfo: (info: Partial<SalaryInfo>) => void
  addTechnicalSkill: (skill: TechnicalSkill) => void
  removeTechnicalSkill: (skillId: string) => void
  updateTechnicalSkill: (skillId: string, updates: Partial<TechnicalSkill>) => void
  setTechnicalSkills: (skills: TechnicalSkill[]) => void
  addBehavioralCompetency: (competency: BehavioralCompetency) => void
  removeBehavioralCompetency: (competencyId: string) => void
  updateBehavioralCompetency: (competencyId: string, updates: Partial<BehavioralCompetency>) => void
  toggleBehavioralCompetency: (competencyId: string) => void
  setBehavioralCompetencies: (competencies: BehavioralCompetency[]) => void
  addWSIQuestion: (question: WSIQuestion) => void
  removeWSIQuestion: (questionId: string) => void
  updateWSIQuestion: (questionId: string, updates: Partial<WSIQuestion>) => void
  setWSIQuestions: (questions: WSIQuestion[]) => void
  setGeneratedJobDescription: (description: string) => void
  updateDetectedCriteria: (criteria: Partial<DetectedCriteria>) => void
  setDetectedCriteria: (criteria: DetectedCriteria) => void
  resetWizard: () => void
  setHasPendingChanges: (value: boolean) => void
  setHasRestoredDraft: (value: boolean) => void
  setCatalogMaturity: (maturity: CatalogMaturity) => void
  setIsLoading: (value: boolean) => void
  canAdvanceStage: () => boolean
  applyOrchestratorUpdates: (updates: OrchestratorFieldUpdates) => void
  applyFastTrackData: (data: FastTrackJobData) => void
  skipToReviewStage: () => void
}

export interface ExpandedChatContextValue extends WizardContextState, WizardContextActions {}

export const INITIAL_DETECTED_CRITERIA: DetectedCriteria = {
  cargo: null,
  gestorArea: null,
  responsabilidades: [],
  competenciasTecnicas: [],
  competenciasComportamentais: [],
  idiomas: [],
  senioridadeIdiomas: null,
  modeloTrabalho: null,
  localizacao: null,
  tipoContrato: null,
  salario: null,
  departamento: null,
  isAffirmative: null,
  affirmativeCriteriaPrimary: null,
  affirmativeCriteriaSecondary: null,
  affirmativeDescription: null,
  experienciaMinima: null,
  formacao: [],
  certificacoes: [],
  ferramentas: [],
  diasPresenciais: null,
  beneficiosMencionados: [],
  bonus: null,
  viagensFrequentes: null,
  disponibilidade: null,
  cnh: null,
  horario: null
}

export const INITIAL_BASIC_INFO_FIELDS: BasicInfoFields = {
  cargo: '',
  area: '',
  gestor: '',
  localidade: '',
  modeloTrabalho: '',
  tipoContrato: ''
}

export const INITIAL_SALARY_INFO: SalaryInfo = {
  minSalary: '',
  maxSalary: '',
  minBonus: '',
  maxBonus: '',
  bonusCriteria: '',
  benefits: [
    { id: '1', name: 'Vale Refeição', value: `${CURRENCY_SYMBOL} 35/dia`, enabled: true },
    { id: '2', name: 'Vale Transporte', enabled: true },
    { id: '3', name: 'Plano de Saúde', enabled: true },
    { id: '4', name: 'Plano Odontológico', enabled: true },
    { id: '5', name: 'Seguro de Vida', enabled: true },
    { id: '6', name: 'Stock Options', enabled: false },
    { id: '7', name: 'Auxílio Home Office', value: `${CURRENCY_SYMBOL} 200/mês`, enabled: true },
    { id: '8', name: 'Auxílio Educação', value: `Até ${CURRENCY_SYMBOL} 500/mês`, enabled: true },
    { id: '9', name: 'Gympass', enabled: false },
    { id: '10', name: 'Day Off Aniversário', enabled: true },
  ]
}

export const DEFAULT_BEHAVIORAL_COMPETENCIES: BehavioralCompetency[] = [
  { id: '1', name: 'Comunicação Eficaz', weight: 4, justification: 'Colaboração com time multidisciplinar', enabled: true },
  { id: '2', name: 'Resolução de Problemas', weight: 5, justification: 'Arquitetura de sistemas complexos', enabled: true },
  { id: '3', name: 'Adaptabilidade', weight: 4, justification: 'Ambiente ágil com mudanças frequentes', enabled: true },
  { id: '4', name: 'Trabalho em Equipe', weight: 4, justification: 'Projetos colaborativos', enabled: true },
  { id: '5', name: 'Proatividade', weight: 3, justification: 'Iniciativa em melhorias técnicas', enabled: false },
]

const ExpandedChatContext = createContext<ExpandedChatContextValue | null>(null)

export function useExpandedChatContext(): ExpandedChatContextValue {
  const context = useContext(ExpandedChatContext)
  if (!context) {
    throw new Error('useExpandedChatContext must be used within an ExpandedChatProvider')
  }
  return context
}

export interface ExpandedChatProviderProps {
  children: ReactNode
  value: ExpandedChatContextValue
}

export function ExpandedChatProvider({ children, value }: ExpandedChatProviderProps) {
  return (
    <ExpandedChatContext.Provider value={value}>
      {children}
    </ExpandedChatContext.Provider>
  )
}

export { ExpandedChatContext }
