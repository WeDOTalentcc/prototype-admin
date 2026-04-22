import React from "react"
import { TemplateSituation } from '@/hooks/chat/use-communication-templates'
import { Users, Building, Video } from "lucide-react"

export type CommunicationType = 'email' | 'whatsapp' | 'triagem' | 'agendamento' | 'feedback' | 'proposta'
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
  initialVacancyId?: string
  initialStage?: string
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
  { value: 'sourcing', label: 'Funil' },
  { value: 'screening', label: 'Triagem' },
  { value: 'interview_hr', label: 'Entrevista RH' },
  { value: 'interview_technical', label: 'Entrevista Técnica' },
  { value: 'interview_manager', label: 'Entrevista Gestor' },
  { value: 'offer', label: 'Proposta' },
  { value: 'hired', label: 'Contratado' },
]

export const platforms = [
  { id: 'zoom', name: 'Zoom', icon: Video },
  { id: 'teams', name: 'Teams', icon: Users },
  { id: 'meet', name: 'Google Meet', icon: Video },
  { id: 'presencial', name: 'Presencial', icon: Building }
] as const
