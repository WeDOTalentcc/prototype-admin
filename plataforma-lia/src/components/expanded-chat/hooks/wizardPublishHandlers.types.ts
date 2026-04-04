"use client"

import React from "react"
import type { ParecerLIAData } from "@/components/chat/parecer-lia-card"
import type {
  TechnicalSkill,
  BehavioralCompetency,
  SalaryInfo,
  DetectedCriteria,
  BasicInfoFields,
} from "../ExpandedChatContext"
import type { WizardStage } from "../config/wizard-config"
import type { Message } from "../types"
import type { PublishingPlatform, JobConfig } from "./usePublishingState"
import type { RecruitmentStage } from "@/components/settings/recruitment-journey.types"
import type { useLearning } from "./useLearning"

export interface WizardPublishHandlersContext {
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
  basicInfoFields: BasicInfoFields
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>

  technicalSkills: TechnicalSkill[]
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  behavioralCompetencies: BehavioralCompetency[]
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>

  salaryInfo: SalaryInfo
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>

  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>

  currentStage: WizardStage
  setCurrentStage: React.Dispatch<React.SetStateAction<WizardStage>>

  publishingPlatforms: PublishingPlatform[]
  jobConfig: JobConfig
  setJobDescription: (desc: string) => void
  setIsGeneratingDescription: (val: boolean) => void

  setPublishedJobId: (id: string | null) => void
  setAwaitingCalibrationChoice: (val: boolean) => void
  setSearchPhase: React.Dispatch<React.SetStateAction<'local-searching' | 'local-complete' | 'global-searching' | 'global-complete' | 'idle'>>
  setLocalCandidateCount: (count: number) => void
  setGlobalCandidateCount: (count: number) => void
  preferredCandidateCount: number

  selectedSuggestedTechnical: Set<string>
  selectedSuggestedBehavioral: Set<string>
  setShowCompetenciesSuggestionsModal: (val: boolean) => void

  clearWizardDraft: () => void
  setHasAppliedRestoredDraft: (val: boolean) => void
  setShowClearDraftConfirm: (val: boolean) => void
  setWsiCandidates: React.Dispatch<React.SetStateAction<any[]>>
  setGeneratedJobDescription: React.Dispatch<React.SetStateAction<string>>

  companyConfig: { values?: string[]; [key: string]: unknown } | null
  interviewStages: RecruitmentStage[]
  companyMembersMap: Map<string, string>
  companyDefaultQuestions: Array<{ enabled: boolean; question: string; type: string }>
  wsiCandidates: Array<{ selected: boolean; question: string; category?: string; expectedAnswer?: unknown; type?: string }>

  user: { name?: string; email?: string; company?: string; id?: string } | null

  wizardFastTrackSourceJobId: string | null
  setWizardFastTrackSourceJobId: (id: string | null) => void

  conversationId: string | null

  learning: ReturnType<typeof useLearning>

  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>

  proceedToNextStage: () => void
}
