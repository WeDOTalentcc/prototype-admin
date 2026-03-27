/**
 * usePublishingState
 *
 * Sprint 4.2 — 2026-03-27
 * Encapsula os ~6 estados relacionados à publicação da vaga (Stage 7.5).
 * Inclui: plataformas, configuração da vaga, job description, idiomas.
 * Padrão { state, actions } compatível com Pinia stores (Vue 3).
 */

import { useState } from 'react'

export interface PublishingPlatform {
  id: string
  name: string
  type: 'ats' | 'jobboard' | 'website'
  enabled: boolean
  logo?: string
}

export interface JobConfig {
  urgencyLevel: number
  visibility: 'public' | 'internal' | 'confidential'
  isConfidential: boolean
  isAffirmative: boolean
  deadline: string
  deadlineScreening: string
  deadlineShortlist: string
  languages: { name: string; level: string }[]
  hybridDaysOnsite?: number
}

const DEFAULT_PUBLISHING_PLATFORMS: PublishingPlatform[] = [
  { id: 'gupy', name: 'Gupy', type: 'ats', enabled: true },
  { id: 'pandape', name: 'Pandapé', type: 'ats', enabled: false },
  { id: 'linkedin', name: 'LinkedIn', type: 'jobboard', enabled: true },
  { id: 'indeed', name: 'Indeed', type: 'jobboard', enabled: false },
  { id: 'website', name: 'Website da Empresa', type: 'website', enabled: true },
]

function createDefaultJobConfig(): JobConfig {
  const now = new Date()
  const deadline = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
  const deadlineScreening = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
  const deadlineShortlist = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000)
  return {
    urgencyLevel: 3,
    visibility: 'public',
    isConfidential: false,
    isAffirmative: false,
    deadline: deadline.toISOString().split('T')[0],
    deadlineScreening: deadlineScreening.toISOString().split('T')[0],
    deadlineShortlist: deadlineShortlist.toISOString().split('T')[0],
    languages: [],
    hybridDaysOnsite: undefined,
  }
}

export interface PublishingStateValues {
  publishingPlatforms: PublishingPlatform[]
  jobConfig: JobConfig
  jobDescription: string
  isGeneratingDescription: boolean
  companyMembersMap: Map<string, string>
  languagesUserEdited: boolean
}

export interface PublishingStateActions {
  setPublishingPlatforms: React.Dispatch<React.SetStateAction<PublishingPlatform[]>>
  setJobConfig: React.Dispatch<React.SetStateAction<JobConfig>>
  setJobDescription: React.Dispatch<React.SetStateAction<string>>
  setIsGeneratingDescription: React.Dispatch<React.SetStateAction<boolean>>
  setCompanyMembersMap: React.Dispatch<React.SetStateAction<Map<string, string>>>
  setLanguagesUserEdited: React.Dispatch<React.SetStateAction<boolean>>
  updateLanguages: (newLanguages: { name: string; level: string }[]) => void
  resetPublishingState: () => void
}

export interface UsePublishingStateReturn {
  state: PublishingStateValues
  actions: PublishingStateActions
}

export function usePublishingState(): UsePublishingStateReturn {
  const [publishingPlatforms, setPublishingPlatforms] = useState<PublishingPlatform[]>(DEFAULT_PUBLISHING_PLATFORMS)
  const [jobConfig, setJobConfig] = useState<JobConfig>(createDefaultJobConfig)
  const [jobDescription, setJobDescription] = useState('')
  const [isGeneratingDescription, setIsGeneratingDescription] = useState(false)
  const [companyMembersMap, setCompanyMembersMap] = useState<Map<string, string>>(new Map())
  const [languagesUserEdited, setLanguagesUserEdited] = useState(false)

  const updateLanguages = (newLanguages: { name: string; level: string }[]) => {
    setLanguagesUserEdited(true)
    setJobConfig(prev => ({ ...prev, languages: newLanguages }))
  }

  const resetPublishingState = () => {
    setPublishingPlatforms(DEFAULT_PUBLISHING_PLATFORMS)
    setJobConfig(createDefaultJobConfig())
    setJobDescription('')
    setIsGeneratingDescription(false)
    setCompanyMembersMap(new Map())
    setLanguagesUserEdited(false)
  }

  return {
    state: {
      publishingPlatforms,
      jobConfig,
      jobDescription,
      isGeneratingDescription,
      companyMembersMap,
      languagesUserEdited,
    },
    actions: {
      setPublishingPlatforms,
      setJobConfig,
      setJobDescription,
      setIsGeneratingDescription,
      setCompanyMembersMap,
      setLanguagesUserEdited,
      updateLanguages,
      resetPublishingState,
    },
  }
}
