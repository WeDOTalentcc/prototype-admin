'use client'

import { useMemo } from 'react'
import {
  type TechnicalSkill,
  type BehavioralCompetency,
  type DetectedCriteria,
} from '../ExpandedChatContext'

export interface WSIQualityField {
  id: string
  label: string
  labelShort: string
  current: number
  required: number
  weight: number
  isMet: boolean
}

export interface WSIQualityGatesResult {
  score: number
  fields: WSIQualityField[]
  missingFields: string[]
  canAdvance: boolean
  summaryText: string
  scoreColor: 'green' | 'yellow' | 'red'
}

export interface UseWSIQualityGatesOptions {
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  detectedCriteria: DetectedCriteria
  generatedJobDescription: string
  minScoreToAdvance?: number
}

const QUALITY_THRESHOLDS = {
  TECHNICAL_SKILLS_MIN: 5,
  TECHNICAL_SKILLS_WEIGHT: 8,
  BEHAVIORAL_MIN: 3,
  BEHAVIORAL_WEIGHT: 10,
  RESPONSIBILITIES_MIN: 3,
  RESPONSIBILITIES_WEIGHT: 5,
  SENIORITY_WEIGHT: 5,
  WORK_MODEL_WEIGHT: 5,
  DESCRIPTION_MIN_CHARS: 200,
  DESCRIPTION_WEIGHT: 5,
}

export function useWSIQualityGates(options: UseWSIQualityGatesOptions): WSIQualityGatesResult {
  const {
    technicalSkills,
    behavioralCompetencies,
    detectedCriteria,
    generatedJobDescription,
    minScoreToAdvance = 70,
  } = options

  return useMemo(() => {
    const enabledBehavioral = behavioralCompetencies.filter(c => c.enabled)
    const responsibilities = detectedCriteria.responsabilidades || []
    const hasSeniority = Boolean(detectedCriteria.senioridadeIdiomas)
    const hasWorkModel = Boolean(detectedCriteria.modeloTrabalho)
    const descriptionLength = generatedJobDescription?.length || 0

    const technicalCount = Math.min(technicalSkills.length, QUALITY_THRESHOLDS.TECHNICAL_SKILLS_MIN)
    const technicalScore = (technicalCount / QUALITY_THRESHOLDS.TECHNICAL_SKILLS_MIN) * QUALITY_THRESHOLDS.TECHNICAL_SKILLS_WEIGHT * QUALITY_THRESHOLDS.TECHNICAL_SKILLS_MIN

    const behavioralCount = Math.min(enabledBehavioral.length, QUALITY_THRESHOLDS.BEHAVIORAL_MIN)
    const behavioralScore = (behavioralCount / QUALITY_THRESHOLDS.BEHAVIORAL_MIN) * QUALITY_THRESHOLDS.BEHAVIORAL_WEIGHT * QUALITY_THRESHOLDS.BEHAVIORAL_MIN

    const responsibilitiesCount = Math.min(responsibilities.length, QUALITY_THRESHOLDS.RESPONSIBILITIES_MIN)
    const responsibilitiesScore = (responsibilitiesCount / QUALITY_THRESHOLDS.RESPONSIBILITIES_MIN) * QUALITY_THRESHOLDS.RESPONSIBILITIES_WEIGHT * QUALITY_THRESHOLDS.RESPONSIBILITIES_MIN

    const seniorityScore = hasSeniority ? QUALITY_THRESHOLDS.SENIORITY_WEIGHT : 0
    const workModelScore = hasWorkModel ? QUALITY_THRESHOLDS.WORK_MODEL_WEIGHT : 0
    const descriptionScore = descriptionLength >= QUALITY_THRESHOLDS.DESCRIPTION_MIN_CHARS ? QUALITY_THRESHOLDS.DESCRIPTION_WEIGHT : 0

    const totalScore = technicalScore + behavioralScore + responsibilitiesScore + seniorityScore + workModelScore + descriptionScore

    const fields: WSIQualityField[] = [
      {
        id: 'technical',
        label: 'Competências Técnicas',
        labelShort: 'Técnicas',
        current: technicalSkills.length,
        required: QUALITY_THRESHOLDS.TECHNICAL_SKILLS_MIN,
        weight: QUALITY_THRESHOLDS.TECHNICAL_SKILLS_WEIGHT * QUALITY_THRESHOLDS.TECHNICAL_SKILLS_MIN,
        isMet: technicalSkills.length >= QUALITY_THRESHOLDS.TECHNICAL_SKILLS_MIN,
      },
      {
        id: 'behavioral',
        label: 'Competências Comportamentais',
        labelShort: 'Comportamentais',
        current: enabledBehavioral.length,
        required: QUALITY_THRESHOLDS.BEHAVIORAL_MIN,
        weight: QUALITY_THRESHOLDS.BEHAVIORAL_WEIGHT * QUALITY_THRESHOLDS.BEHAVIORAL_MIN,
        isMet: enabledBehavioral.length >= QUALITY_THRESHOLDS.BEHAVIORAL_MIN,
      },
      {
        id: 'responsibilities',
        label: 'Responsabilidades',
        labelShort: 'Responsabilidades',
        current: responsibilities.length,
        required: QUALITY_THRESHOLDS.RESPONSIBILITIES_MIN,
        weight: QUALITY_THRESHOLDS.RESPONSIBILITIES_WEIGHT * QUALITY_THRESHOLDS.RESPONSIBILITIES_MIN,
        isMet: responsibilities.length >= QUALITY_THRESHOLDS.RESPONSIBILITIES_MIN,
      },
      {
        id: 'seniority',
        label: 'Senioridade',
        labelShort: 'Senioridade',
        current: hasSeniority ? 1 : 0,
        required: 1,
        weight: QUALITY_THRESHOLDS.SENIORITY_WEIGHT,
        isMet: hasSeniority,
      },
      {
        id: 'workModel',
        label: 'Modelo de Trabalho',
        labelShort: 'Modelo',
        current: hasWorkModel ? 1 : 0,
        required: 1,
        weight: QUALITY_THRESHOLDS.WORK_MODEL_WEIGHT,
        isMet: hasWorkModel,
      },
      {
        id: 'description',
        label: 'Descrição Detalhada',
        labelShort: 'Descrição',
        current: descriptionLength >= QUALITY_THRESHOLDS.DESCRIPTION_MIN_CHARS ? 1 : 0,
        required: 1,
        weight: QUALITY_THRESHOLDS.DESCRIPTION_WEIGHT,
        isMet: descriptionLength >= QUALITY_THRESHOLDS.DESCRIPTION_MIN_CHARS,
      },
    ]

    const missingFields = fields
      .filter(f => !f.isMet)
      .map(f => f.label)

    const scoreColor: 'green' | 'yellow' | 'red' = 
      totalScore >= 70 ? 'green' : 
      totalScore >= 50 ? 'yellow' : 
      'red'

    const summaryParts: string[] = []
    const techField = fields.find(f => f.id === 'technical')!
    const behavField = fields.find(f => f.id === 'behavioral')!
    const senField = fields.find(f => f.id === 'seniority')!

    summaryParts.push(`${techField.current}/${techField.required} Técnicas`)
    summaryParts.push(`${behavField.current}/${behavField.required} Comportamentais`)
    if (senField.isMet) {
      summaryParts.push('Senioridade ✓')
    }

    const score = Math.min(Math.round(totalScore), 100)

    return {
      score,
      fields,
      missingFields,
      canAdvance: score >= minScoreToAdvance,
      summaryText: summaryParts.join(' • '),
      scoreColor,
    }
  }, [technicalSkills, behavioralCompetencies, detectedCriteria, generatedJobDescription, minScoreToAdvance])
}
