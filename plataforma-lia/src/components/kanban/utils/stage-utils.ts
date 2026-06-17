import { RECRUITMENT_STAGES, type RecruitmentStage } from "@/lib/recruitment/stages-data"
import type { DynamicStage, InterviewStageFromJob, CandidatesDataMap, KanbanCandidate } from "../types"
import type { SubStatusOption } from "@/components/settings/recruitment-journey.types"
import { 
  DYNAMIC_STAGE_COLORS, 
  SYSTEM_INITIAL_STAGES, 
  SYSTEM_FINAL_STAGES,
  LEGACY_STAGE_MAPPING 
} from "../constants"

const STAGE_ACTION_BEHAVIOR_MAP: Record<string, string> = {
  'standby': 'standby',
  'stand_by': 'standby',
  'long_list': 'passive',
  'short_list': 'passive',
  'interview_hr': 'scheduling',
  'entrevista_rh': 'scheduling',
  'technical_test': 'evaluation',
  'teste_tecnico': 'evaluation',
  'english_test': 'evaluation',
  'teste_de_ingles': 'evaluation',
  'interview_technical': 'scheduling',
  'entrevista_tecnica': 'scheduling',
  'interview_manager': 'scheduling',
  'entrevista_gestor': 'scheduling',
  'interview_manager2': 'scheduling',
  'entrevista_gestor_2': 'scheduling',
  'interview_final': 'scheduling',
  'entrevista_final': 'scheduling',
  'references': 'verification',
  'referencias': 'verification',
  'offer': 'offer',
  'proposta': 'offer',
}

const STAGE_TYPE_BEHAVIOR_MAP: Record<string, string> = {
  'interview': 'scheduling',
  'test': 'evaluation',
  'automated': 'evaluation',
}

function inferActionBehavior(stageSlug: string, stageType?: string): string {
  if (STAGE_ACTION_BEHAVIOR_MAP[stageSlug]) {
    return STAGE_ACTION_BEHAVIOR_MAP[stageSlug]
  }

  if (stageSlug.includes('entrevista') || stageSlug.includes('interview')) return 'scheduling'
  if (stageSlug.includes('teste') || stageSlug.includes('test')) return 'evaluation'
  if (stageSlug.includes('referencia') || stageSlug.includes('reference')) return 'verification'
  if (stageSlug.includes('proposta') || stageSlug.includes('offer')) return 'offer'

  if (stageType && STAGE_TYPE_BEHAVIOR_MAP[stageType]) {
    return STAGE_TYPE_BEHAVIOR_MAP[stageType]
  }

  return 'passive'
}

export function createStageSlug(stageName: string): string {
  return stageName
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

export function mapInterviewStagesToKanban(
  interviewStages?: InterviewStageFromJob[],
  fallbackStages: RecruitmentStage[] = RECRUITMENT_STAGES
): DynamicStage[] {
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
  
  const allStages = [
    ...SYSTEM_INITIAL_STAGES,
    ...customStages,
    ...SYSTEM_FINAL_STAGES
  ]
  
  return allStages.sort((a, b) => a.order - b.order)
}

export function organizeCandidatesByDynamicStages(
  candidates: KanbanCandidate[],
  stages: DynamicStage[]
): CandidatesDataMap {
  const organized: CandidatesDataMap = {}
  stages.forEach(stage => {
    organized[stage.id] = []
  })
  
  candidates.forEach(candidate => {
    const rawStage = (candidate.stage || candidate.status || 'sourcing').toLowerCase().trim()
    let targetStageId = LEGACY_STAGE_MAPPING[rawStage] || rawStage
    
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

export function createInitialCandidatesData(stages: DynamicStage[]): CandidatesDataMap {
  const data: CandidatesDataMap = {}
  stages.forEach(stage => {
    data[stage.id] = []
  })
  return data
}

export function getStageById(stages: DynamicStage[], stageId: string): DynamicStage | undefined {
  return stages.find(s => s.id === stageId)
}

export function isTransitionAllowed(
  fromStage: DynamicStage,
  toStage: DynamicStage,
  allowedTransitions?: string[]
): boolean {
  if (!allowedTransitions) return true
  return allowedTransitions.includes(toStage.id)
}

export function getActiveStages(stages: DynamicStage[]): DynamicStage[] {
  return stages.filter(s => s.stageType === 'active')
}

export function getFinalStages(stages: DynamicStage[]): DynamicStage[] {
  return stages.filter(s => s.stageType === 'final')
}

/**
 * Builds a map of stage name → active sub-statuses from the company pipeline response.
 * Used to enrich DynamicStages with sub_statuses from the DB.
 */
export function buildSubStatusMap(
  pipeline: Array<{ name: string; sub_statuses?: SubStatusOption[] }>
): Record<string, SubStatusOption[]> {
  const map: Record<string, SubStatusOption[]> = {}
  for (const stage of pipeline) {
    if (stage.name && Array.isArray(stage.sub_statuses) && stage.sub_statuses.length > 0) {
      map[stage.name] = stage.sub_statuses
    }
  }
  return map
}

/**
 * Enriches DynamicStage[] with subStatuses from the company pipeline map.
 * Falls back to empty array for stages not found in the map.
 */
export function enrichStagesWithSubStatuses(
  stages: DynamicStage[],
  subStatusMap: Record<string, SubStatusOption[]>
): DynamicStage[] {
  if (!Object.keys(subStatusMap).length) return stages
  return stages.map(stage => ({
    ...stage,
    subStatuses: subStatusMap[stage.name] ?? stage.subStatuses,
  }))
}

/**
 * #5 Fase 2: sobrepõe o override de sub-status POR VAGA sobre o mapa da empresa.
 * Override vive em job.interview_stages[].subStatuses (persistido no JSON da vaga).
 * Etapa sem override mantém o default herdado da empresa.
 * Consumer-first: chamado nos call sites do kanban ANTES de enrichStagesWithSubStatuses,
 * para que o seletor de sub-status da transição reflita a customização da vaga.
 */
export function applyVacancyStageOverrides(
  subStatusMap: Record<string, SubStatusOption[]>,
  jobInterviewStages?: Array<{ name?: string; stageName?: string; subStatuses?: SubStatusOption[] }>
): Record<string, SubStatusOption[]> {
  if (!Array.isArray(jobInterviewStages) || jobInterviewStages.length === 0) return subStatusMap
  const merged = { ...subStatusMap }
  for (const st of jobInterviewStages) {
    const key = st?.name || st?.stageName
    if (key && Array.isArray(st.subStatuses) && st.subStatuses.length > 0) {
      merged[key] = st.subStatuses
    }
  }
  return merged
}
