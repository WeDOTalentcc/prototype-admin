import React from "react"
import { TemplateSituation } from '@/hooks/chat/use-communication-templates'
import { Briefcase, FileText, Users, Building, Video } from "lucide-react"

export type CommunicationType = 'email' | 'whatsapp' | 'triagem' | 'agendamento' | 'feedback'
export type CommunicationChannel = 'email' | 'whatsapp' | 'both'

export interface Candidate {
  id: string
  name: string
  role: string
  email: string
  phone: string
  location?: string
  avatar?: string
  score?: number
  matchPercentage?: number
  skills?: string[]
}

export interface UnifiedCommunicationModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  type: CommunicationType
  jobTitle?: string
  onSend?: (data: CommunicationResult) => void
  companyId: string
  selectedCandidates?: Array<{ id: string; name: string; email?: string; phone?: string; avatar?: string }>
  situation?: TemplateSituation
  aiFeedbackContext?: { vacancyCandidateId: string; toStage: string; subStatus?: string | null } | null
}

export interface CommunicationResult {
  type: CommunicationType
  channel: CommunicationChannel
  message: string
  subject?: string
  recipient: string
  metadata?: Record<string, unknown>
}

export interface Template {
  id: string
  name: string
  subject?: string
  message: string
  icon?: React.ReactNode
}

export interface InterviewSettings {
  interviewType: 'funcional' | 'tecnica' | 'completa' | 'cultural'
  platform: 'zoom' | 'teams' | 'meet' | 'presencial'
  duration: string
  date: string
  time: string
  interviewer: string
}

export interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
  status?: string
}

export const PIPELINE_STAGES = [
  { value: 'novo', label: 'Novo' },
  { value: 'triagem', label: 'Triagem' },
  { value: 'entrevista', label: 'Entrevista' },
  { value: 'avaliacao', label: 'Avaliação' },
  { value: 'oferta', label: 'Oferta' }
]

export const interviewTypes: Array<{ id: string; name: string; description: string; icon: React.ElementType; disabled?: boolean }> = [
  { id: 'funcional', name: 'Funcional', description: 'Avaliação de competências da função', icon: Briefcase },
  { id: 'tecnica', name: 'Técnica', description: 'Avaliação de skills técnicos', icon: FileText, disabled: true },
  { id: 'completa', name: 'Completa', description: 'Avaliação abrangente', icon: Users, disabled: true },
  { id: 'cultural', name: 'Cultural', description: 'Fit cultural e valores', icon: Building, disabled: true },
]

export const platforms = [
  { id: 'zoom', name: 'Zoom', icon: Video },
  { id: 'teams', name: 'Teams', icon: Users },
  { id: 'meet', name: 'Google Meet', icon: Video },
  { id: 'presencial', name: 'Presencial', icon: Building }
] as const

export const interviewers = [
  'Ana Silva - Recrutadora Sênior',
  'Carlos Mendes - Tech Lead',
  'Marina Costa - Gerente de Produto',
  'Roberto Santos - RH'
]
