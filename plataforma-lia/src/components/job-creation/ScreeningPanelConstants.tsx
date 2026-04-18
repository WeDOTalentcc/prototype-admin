"use client"

import React from "react"
import {
  Brain, MessageCircle, FileText, Building2, Zap, Users
} from "lucide-react"
import {
  WSI_BLOCKS as CANONICAL_WSI_BLOCKS,
  WSI_AUTOMATIC_MESSAGES as CANONICAL_WSI_MESSAGES,
  formatMessageWithVariables as canonicalFormatMessage,
  type WSIBlock as CanonicalWSIBlock,
} from "@/constants/wsi-blocks"
import type { BigFiveProfile } from "@/hooks/recruitment/use-screening-questions"

export interface ScreeningQuestionsPanelProps {
  jobTitle: string
  department?: string
  seniority: 'junior' | 'pleno' | 'senior' | 'lead' | 'executive'
  bigFiveProfile?: BigFiveProfile
  skills: string[]
  behavioralCompetencies?: string[]
  isAffirmative?: boolean
  affirmativeType?: string
  onQuestionsChange?: (questions: Record<string, unknown>[]) => void
  className?: string
}

/**
 * Mapeamento iconName (canônico) → componente Lucide.
 * Audit P2-1/NEW-3: a fonte canônica `@/constants/wsi-blocks.ts` é
 * pura/serializável; o ícone é injetado aqui no client-only.
 */
const ICON_BY_NAME: Record<NonNullable<CanonicalWSIBlock['iconName']>, React.ElementType> = {
  MessageCircle,
  FileText,
  Building2,
  Zap,
  Users,
  Brain,
}

export type WSIBlockWithIcon = CanonicalWSIBlock & { icon: React.ElementType }

/** Re-export enriquecido com componentes de ícone para consumo no client. */
export const WSI_BLOCKS: WSIBlockWithIcon[] = CANONICAL_WSI_BLOCKS.map((b) => ({
  ...b,
  icon: b.iconName ? ICON_BY_NAME[b.iconName] : Brain,
}))

export const WSI_AUTOMATIC_MESSAGES = CANONICAL_WSI_MESSAGES
export const formatMessageWithVariables = canonicalFormatMessage
