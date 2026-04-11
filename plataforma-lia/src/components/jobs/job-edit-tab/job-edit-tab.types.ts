"use client"

import React from "react"
import type { CompanyDefaults } from "@/hooks/company/use-company-defaults"

export interface JobEditTabProps {
  jobEditForm: Record<string, unknown>
  setJobEditForm: React.Dispatch<React.SetStateAction<Record<string, unknown>>>
  onSaveSection: (sectionId: string, fields: string[]) => Promise<void>
  savingSection: string | null
  companyDefaults?: CompanyDefaults
  job?: Record<string, unknown>
  onJobUpdate?: (updatedJob: Record<string, unknown>) => void
  onFormUpdate?: (updates: Record<string, unknown>) => void
  isCreationMode?: boolean
  onPublish?: () => void
  isPublishing?: boolean
  publicLink?: string | null
}

export type StageItem = {
  stageName: string
  order: number
  type: string
  stageCategory?: string
  name?: string
  isEditable?: boolean
  isRemovable?: boolean
  isReorderable?: boolean
  slaDays?: number
  defaultSlaDays?: number
  liaAssisted?: boolean
  isActive?: boolean
}

export type ScreeningImpact = "pause" | "complete" | "ask_reactivate" | "none"

export interface StatusChangeConfirm {
  newStatus: string
  screeningImpact: ScreeningImpact
}
