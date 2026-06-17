import {
  RECRUITMENT_STAGES,
  type RecruitmentStage,
} from "@/lib/recruitment/stages-data"

export interface InterviewStageFromJob {
  stageName: string
  order: number
  sla?: number
  type: 'automated' | 'manual' | 'hybrid' | 'system' | 'interview' | 'test' | 'custom'
}

// Enriched stage returned by the backend (superset of InterviewStageFromJob)
interface EnrichedInterviewStage extends InterviewStageFromJob {
  stageCategory?: string
  displayName?: string
  name?: string
  isInitial?: boolean
  isFinal?: boolean
  isHired?: boolean
  isRejection?: boolean
  isActive?: boolean
  stageType?: 'active' | 'final'
  color?: string
  actionBehavior?: string
}

export interface DynamicStage {
  id: string
  name: string
  displayName: string
  order: number
  color: string
  stageType: 'active' | 'final'
  isInitial?: boolean
  isFinal?: boolean
  isHired?: boolean
  isRejection?: boolean
  isActive?: boolean
  actionBehavior?: string
}

export const createStageSlug = (stageName: string): string => {
  return stageName
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

export const DYNAMIC_STAGE_COLORS = [
  'var(--lia-text-secondary)',
  'var(--lia-text-secondary)',
  'var(--lia-text-tertiary)',
  'var(--lia-text-tertiary)',
  'var(--lia-text-tertiary)',
  'var(--lia-text-secondary)',
  'var(--lia-text-secondary)',
]

export const inferActionBehavior = (slug: string, stageType?: string): string => {
  const map: Record<string, string> = {
    'sourcing': 'intake', 'screening': 'screening',
    'long_list': 'passive', 'short_list': 'passive',
    'interview_hr': 'scheduling', 'entrevista_rh': 'scheduling',
    'interview_technical': 'scheduling', 'entrevista_tecnica': 'scheduling',
    'interview_manager': 'scheduling', 'entrevista_gestor': 'scheduling',
    'interview_manager2': 'scheduling', 'entrevista_gestor_2': 'scheduling',
    'interview_final': 'scheduling', 'entrevista_final': 'scheduling',
    'technical_test': 'evaluation', 'teste_tecnico': 'evaluation',
    'english_test': 'evaluation', 'teste_de_ingles': 'evaluation',
    'references': 'verification', 'referencias': 'verification',
    'offer': 'offer', 'proposta': 'offer',
    'hired': 'conclusion_hired', 'rejected': 'conclusion_rejected',
    'offer_declined': 'conclusion_declined',
  }
  if (map[slug]) return map[slug]
  if (slug.includes('entrevista') || slug.includes('interview')) return 'scheduling'
  if (slug.includes('teste') || slug.includes('test')) return 'evaluation'
  if (slug.includes('referencia') || slug.includes('reference')) return 'verification'
  if (slug.includes('proposta') || slug.includes('offer')) return 'offer'
  if (stageType === 'interview') return 'scheduling'
  if (stageType === 'test' || stageType === 'automated') return 'evaluation'
  return 'passive'
}

export const mapInterviewStagesToKanban = (
  interviewStages?: InterviewStageFromJob[],
  fallbackStages: RecruitmentStage[] = RECRUITMENT_STAGES
): DynamicStage[] => {
  if (interviewStages && interviewStages.length > 0 && (interviewStages[0] as EnrichedInterviewStage).stageCategory) {
    const enrichedStages = interviewStages as EnrichedInterviewStage[]
    const activeStages = enrichedStages.filter((s) => s.isActive !== false)
    let colorIndex = 0
    return activeStages
      .sort((a, b) => (a.order || 0) - (b.order || 0))
      .map((stage) => {
        const displayName = stage.stageName || stage.displayName || stage.name || 'Sem nome'
        const stageId = stage.name || createStageSlug(displayName)
        const isIntermediate = !stage.isInitial && !stage.isFinal && stage.stageType === 'active'
        const color = stage.color || (isIntermediate ? DYNAMIC_STAGE_COLORS[colorIndex++ % DYNAMIC_STAGE_COLORS.length] : 'var(--lia-text-secondary)')
        return {
          id: stageId,
          name: stageId,
          displayName,
          order: stage.order,
          color,
          stageType: stage.stageType || 'active',
          isInitial: stage.isInitial || false,
          isFinal: stage.isFinal || false,
          isHired: stage.isHired || false,
          isRejection: stage.isRejection || false,
          actionBehavior: stage.actionBehavior || inferActionBehavior(stageId),
        }
      })
  }

  if (!interviewStages || interviewStages.length === 0) {
    return fallbackStages
      .filter(stage => stage.stageType !== 'standby')
      .map((stage) => ({
        id: stage.name,
        name: stage.name,
        displayName: stage.displayName,
        order: stage.stageOrder,
        color: stage.color,
        stageType: stage.stageType === 'standby' ? 'active' : stage.stageType,
        isInitial: stage.isInitial,
        isFinal: stage.isFinal,
        isHired: stage.isHired,
        isRejection: stage.isRejection,
        actionBehavior: inferActionBehavior(stage.name)
      }))
  }

  const systemInitialStages = [
    { id: 'sourcing', name: 'sourcing', displayName: 'Funil', order: 0, stageType: 'active' as const, isInitial: true, actionBehavior: 'intake' },
    { id: 'screening', name: 'screening', displayName: 'Triagem', order: 1, color: 'var(--lia-text-secondary)', stageType: 'active' as const, isInitial: false, actionBehavior: 'screening' }
  ] as DynamicStage[]
  const systemFinalStages = [
    { id: 'hired', name: 'hired', displayName: 'Contratado', order: 900, stageType: 'final' as const, isFinal: true, isHired: true, actionBehavior: 'conclusion_hired' },
    { id: 'rejected', name: 'rejected', displayName: 'Reprovado', order: 901, stageType: 'final' as const, isFinal: true, isRejection: true, actionBehavior: 'conclusion_rejected' },
    { id: 'offer_declined', name: 'offer_declined', displayName: 'Proposta Recusada', order: 902, stageType: 'final' as const, isFinal: true, actionBehavior: 'conclusion_declined' }
  ] as DynamicStage[]
  const customStages: DynamicStage[] = interviewStages
    .filter(stage => {
      const slug = createStageSlug(stage.stageName)
      return !['sourcing', 'screening', 'triagem', 'hired', 'rejected', 'offer_declined'].includes(slug)
    })
    .sort((a, b) => a.order - b.order)
    .map((stage, index) => {
      const slug = createStageSlug(stage.stageName)
      return {
        id: slug,
        name: slug,
        displayName: stage.stageName,
        order: stage.order + 10,
        color: DYNAMIC_STAGE_COLORS[index % DYNAMIC_STAGE_COLORS.length],
        stageType: 'active' as const,
        isInitial: false,
        isFinal: false,
        actionBehavior: inferActionBehavior(slug, stage.type)
      }
    })
  return [...systemInitialStages, ...customStages, ...systemFinalStages].sort((a, b) => a.order - b.order)
}

export const organizeCandidatesByDynamicStages = (
  candidates: Record<string, unknown>[],
  stages: DynamicStage[]
): Record<string, Record<string, unknown>[]> => {
  const organized: Record<string, Record<string, unknown>[]> = {}
  stages.forEach(stage => {
    organized[stage.id] = []
  })
  
  const legacyMapping: Record<string, string> = {
    'funil': 'sourcing',
    'triagem': 'screening',
    'entrevista': 'interview_hr',
    'entrevista_rh': 'interview_hr',
    'entrevista_tecnica': 'interview_technical',
    'entrevista_gestor': 'interview_manager',
    'final': 'offer',
    'proposta': 'offer',
    'aprovados': 'hired',
    'contratado': 'hired',
    'reprovados': 'rejected',
    'reprovado': 'rejected',
    'proposta_recusada': 'offer_declined'
  }
  
  candidates.forEach(candidate => {
    const rawStage = String(candidate.stage || candidate.status || 'sourcing').toLowerCase().trim()
    let targetStageId = legacyMapping[rawStage] || rawStage
    
    if (!organized[targetStageId]) {
      const matchingStage = stages.find(s => 
        s.displayName.toLowerCase() === rawStage ||
        s.name.toLowerCase() === rawStage ||
        createStageSlug(s.displayName) === createStageSlug(rawStage)
      )
      if (matchingStage) {
        targetStageId = matchingStage.id
      } else {
        targetStageId = 'sourcing'
      }
    }
    
    if (!organized[targetStageId]) {
      organized[targetStageId] = []
    }
    
    organized[targetStageId].push({
      ...candidate,
      stage: targetStageId
    })
  })
  
  return organized
}

export const createInitialCandidatesData = (stages: DynamicStage[]): Record<string, Record<string, unknown>[]> => {
  const data: Record<string, Record<string, unknown>[]> = {}
  stages.forEach(stage => {
    data[stage.id] = []
  })
  return data
}
