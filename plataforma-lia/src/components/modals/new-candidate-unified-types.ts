import type React from 'react'
import type { DuplicateCheckResult } from '@/services/duplicate-detection-service'

export const ACCEPTED_FILE_TYPES: Record<string, string[]> = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
}

export { MAX_FILE_SIZE } from '@/constants/upload'

export interface ParsedCV {
  full_name: string
  email?: string
  phone?: string
  linkedin?: string
  github?: string
  portfolio?: string
  location?: string
  current_title?: string
  seniority_level?: string
  summary?: string
  experiences: Array<{
    company: string
    title: string
    start_date?: string
    end_date?: string
    is_current: boolean
    description?: string
    location?: string
  }>
  education: Array<{
    institution: string
    degree?: string
    field_of_study?: string
    start_date?: string
    end_date?: string
    is_completed: boolean
    description?: string
  }>
  skills: string[]
  languages: string[]
  certifications: string[]
  raw_text: string
  file_name?: string
  file_type?: string
  file_size_bytes?: number
  confidence_score: number
  extraction_notes: string[]
  parsed_at: string
}

export interface ParsedCVResponse {
  success: boolean
  message: string
  parsed_cv: ParsedCV | null
  duplicate_warning?: {
    message: string
    existing_candidate_id: string
    existing_candidate_name: string
    match_type: string
    similarity_score: number
  } | null
  candidate_id?: string | null
}

export interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
}

export interface NewCandidateUnifiedModalProps {
  isOpen: boolean
  onClose: () => void
  onCandidateAdded: (candidate: Record<string, unknown>) => void
  jobVacancies?: JobVacancy[]
  candidateLists?: Array<{ id: string; name: string; color?: string }>
  preSelectedListId?: string
  preSelectedListName?: string
  onGoToSearch?: () => void
  onOpenFullProfile?: (candidateId: string) => void
}

export type Step = 'input' | 'duplicate-found' | 'processing' | 'success'
export type InputTab = 'cv' | 'linkedin' | 'manual'

export interface ManualData {
  name: string
  email: string
  phone: string
  linkedinUrl: string
}

export interface UseNewCandidateModalReturn {
  currentStep: Step
  setCurrentStep: (step: Step) => void
  activeTab: InputTab
  setActiveTab: (tab: InputTab) => void
  isDragging: boolean
  selectedFile: File | null
  setSelectedFile: (file: File | null) => void
  cvText: string
  setCvText: (text: string) => void
  isProcessing: boolean
  isEnriching: boolean
  uploadProgress: number
  error: string | null
  setError: (error: string | null) => void
  parsedCV: ParsedCV | null
  linkedinUrl: string
  setLinkedinUrl: (url: string) => void
  manualData: ManualData
  setManualData: React.Dispatch<React.SetStateAction<ManualData>>
  duplicateResult: DuplicateCheckResult | null
  setDuplicateResult: (result: DuplicateCheckResult | null) => void
  savedCandidateId: string
  canSubmitCV: boolean
  canSubmitLinkedin: boolean
  canSubmitManual: boolean
  handleDragEnter: (e: React.DragEvent) => void
  handleDragLeave: (e: React.DragEvent) => void
  handleDragOver: (e: React.DragEvent) => void
  handleDrop: (e: React.DragEvent) => void
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleSubmitCV: () => Promise<void>
  handleSubmitLinkedin: () => Promise<void>
  handleSubmitManual: () => Promise<void>
  handleOpenExistingCandidate: () => void
  handleCreateAnyway: () => Promise<void>
}
