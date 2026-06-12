"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Lock, Shield, Settings } from "lucide-react"
import type { RecruitmentStage, StageDataField } from "./recruitment-journey.types"

export function getTypeBadge(type: RecruitmentStage['type']) {
  switch (type) {
    case 'system':
      return <TypeBadge tKey="typeSystem" Icon={Lock} className="bg-lia-interactive-active text-lia-text-secondary" />
    case 'default':
      return <TypeBadge tKey="typeDefault" Icon={Shield} className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary" />
    case 'custom':
      return <TypeBadge tKey="typeCustom" Icon={Settings} className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary" />
  }
}

function TypeBadge({ tKey, Icon, className }: { tKey: string; Icon: React.ComponentType<{ className?: string }>; className: string }) {
  const t = useTranslations("settings.stageHelpers")
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${className} text-micro font-medium`}>
      <Icon className="h-3 w-3" />
      {t(tKey)}
    </span>
  )
}

const ACTION_BEHAVIOR_LABELS: Record<string, string> = {
  intake: "Entrada", screening: "Triagem WSI", scheduling: "Agendamento",
  evaluation: "Avaliação", verification: "Verificação", offer: "Proposta",
  passive: "Passivo", conclusion_hired: "Contratação",
  conclusion_rejected: "Reprovação", conclusion_declined: "Proposta Recusada",
}

const ACTION_BEHAVIOR_SHORT: Record<string, string> = {
  intake: "Entrada", screening: "Triagem", scheduling: "Agend.",
  evaluation: "Aval.", verification: "Verif.", offer: "Proposta",
  passive: "Passivo", conclusion_hired: "Contrat.",
  conclusion_rejected: "Reprov.", conclusion_declined: "Recusada",
}

// TODO P2-W1-02: action_behavior é string field (não enum tipado). Os valores canonicos
// (passive, screening, scheduling, evaluation, offer, etc.) estao espalhados pelo código.
// Próximo passo: consumir via GET /stage-catalog que retorna action_behavior por stage.
// Centralizar enum em recruitment-types.ts e importar aqui.
export function getActionBehaviorLabel(behavior?: string): string | null {
  return behavior ? (ACTION_BEHAVIOR_LABELS[behavior] || null) : null
}

export function getActionBehaviorShort(behavior?: string): string | null {
  return behavior ? (ACTION_BEHAVIOR_SHORT[behavior] || null) : null
}

export function ActionBehaviorBadge({ behavior }: { behavior?: string }) {
  const t = useTranslations("settings.stageHelpers")
  const BEHAVIOR_KEYS: Record<string, string> = {
    intake: "behaviorIntake",
    screening: "behaviorScreening",
    scheduling: "behaviorScheduling",
    evaluation: "behaviorEvaluation",
    verification: "behaviorVerification",
    offer: "behaviorOffer",
    passive: "behaviorPassive",
    conclusion_hired: "behaviorHired",
    conclusion_rejected: "behaviorRejected",
    conclusion_declined: "behaviorDeclined",
  }
  if (!behavior || !BEHAVIOR_KEYS[behavior]) return null
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-cyan/15 text-wedo-cyan">
      {t(BEHAVIOR_KEYS[behavior])}
    </span>
  )
}

export function getStageDisplayName(stage: RecruitmentStage): string {
  return stage.display_name || stage.name
}

// Names of canonical default stages that have locale-aware translations.
const DEFAULT_STAGE_NAME_KEYS = new Set([
  'sourcing', 'screening', 'long_list', 'short_list', 'interview_hr',
  'technical_test', 'english_test', 'interview_technical',
  'interview_manager', 'interview_final', 'references',
  'offer', 'offer_declined', 'hired', 'rejected',
])

/**
 * Returns a function that resolves a stage's display name with i18n support.
 * For known default stages (matched by `name`), it returns the locale-specific
 * label from `settings.recruitment.journey.defaultStageNames.<name>`. For any
 * other stage (custom user-added or API-provided), it falls back to the raw
 * `display_name` so user input is preserved as-is.
 */
export function useStageDisplayName(): (stage: RecruitmentStage) => string {
  const t = useTranslations("settings.recruitment.journey.defaultStageNames")
  return (stage: RecruitmentStage) => {
    if (stage.name && DEFAULT_STAGE_NAME_KEYS.has(stage.name)) {
      return t(stage.name as never) as string
    }
    return stage.display_name || stage.name
  }
}

export function isRealId(id: string): boolean {
  return !id.startsWith('stage-') && !id.startsWith('catalog-')
}
