import {
  RECRUITMENT_STAGES,
  LIA_ASSISTED_STAGES,
  DEFAULT_SLA_DAYS,
  type RecruitmentStage,
  type CompanyPipelineStage,
  type StageType,
  type StatusCategory,
} from './stages-data'
import { SUB_STATUSES, TEST_STATUSES, DOCUMENT_STATUSES, type SubStatus } from './sub-statuses-data'

export function getCompanyPipelineStages(): CompanyPipelineStage[] {
  return RECRUITMENT_STAGES
    .filter(s => s.name !== 'standby' && s.name !== 'interview_manager2')
    .map((stage, index) => ({
      name: stage.name,
      displayName: stage.displayName,
      stageOrder: index + 1,
      color: stage.color,
      icon: stage.icon,
      stageType: stage.stageType,
      stageCategory: stage.stageCategory,
      isInitial: stage.isInitial,
      isFinal: stage.isFinal,
      isHired: stage.isHired,
      isRejection: stage.isRejection,
      isStandby: stage.isStandby,
      isActive: true,
      isEditable: stage.stageCategory !== 'system',
      isRemovable: stage.stageCategory === 'custom',
      isReorderable: stage.stageCategory !== 'system',
      defaultSlaDays: DEFAULT_SLA_DAYS[stage.name] || 3,
      liaAssisted: LIA_ASSISTED_STAGES.includes(stage.name),
    }))
}

export function getJobPipelineStages(pipelineStages?: CompanyPipelineStage[]): CompanyPipelineStage[] {
  const stages = pipelineStages || getCompanyPipelineStages()
  return stages.filter(s => s.isActive)
}

export function getEditableJobStages(pipelineStages?: CompanyPipelineStage[]): CompanyPipelineStage[] {
  const stages = getJobPipelineStages(pipelineStages)
  return stages.filter(s => !s.isInitial && !s.isFinal && s.stageType === 'active')
}

export function getStageByName(name: string): RecruitmentStage | undefined {
  return RECRUITMENT_STAGES.find(stage => stage.name === name)
}

export function getSubStatusesByStage(stageName: string): SubStatus[] {
  return SUB_STATUSES[stageName] || []
}

export function getSubStatusDisplayName(stageName: string, subStatusName: string): string {
  const subStatuses = SUB_STATUSES[stageName]
  if (!subStatuses) return subStatusName
  const subStatus = subStatuses.find(s => s.name === subStatusName)
  return subStatus?.displayName || subStatusName
}

export function getTestStatusesByType(testType: string): SubStatus[] {
  return TEST_STATUSES[testType] || []
}

export function getAllSubStatuses(): SubStatus[] {
  const allStatuses: SubStatus[] = []
  Object.values(SUB_STATUSES).forEach(statuses => allStatuses.push(...statuses))
  Object.values(TEST_STATUSES).forEach(statuses => allStatuses.push(...statuses))
  allStatuses.push(...DOCUMENT_STATUSES)
  return allStatuses
}

export function mapLegacyStage(legacyStatus: string): string {
  const mapping: Record<string, string> = {
    'novo': 'sourcing', 'new': 'sourcing', 'triagem': 'screening', 'screening': 'screening',
    'entrevista': 'interview_hr', 'interview': 'interview_hr', 'tecnica': 'interview_technical',
    'technical': 'interview_technical', 'gestor': 'interview_manager', 'manager': 'interview_manager',
    'final': 'interview_final', 'proposta': 'offer', 'offer': 'offer', 'contratado': 'hired',
    'hired': 'hired', 'reprovado': 'rejected', 'rejected': 'rejected', 'recusado': 'offer_declined',
    'declined': 'offer_declined', 'standby': 'standby', 'banco': 'standby',
  }
  return mapping[legacyStatus.toLowerCase()] || 'sourcing'
}

export function getDefaultSubStatus(stageName: string): SubStatus | undefined {
  const subStatuses = SUB_STATUSES[stageName]
  if (!subStatuses) return undefined
  return subStatuses.find(s => s.isDefault) || subStatuses[0]
}

export function getApprovalSubStatuses(stageName: string): SubStatus[] {
  const subStatuses = SUB_STATUSES[stageName]
  if (!subStatuses) return []
  return subStatuses.filter(s => s.isApproval)
}

export function getRejectionSubStatuses(stageName: string): SubStatus[] {
  const subStatuses = SUB_STATUSES[stageName]
  if (!subStatuses) return []
  return subStatuses.filter(s => s.isRejection)
}

export function getWaitingSubStatuses(stageName: string): SubStatus[] {
  const subStatuses = SUB_STATUSES[stageName]
  if (!subStatuses) return []
  return subStatuses.filter(s => s.isWaiting)
}

export type { StageType, StatusCategory, RecruitmentStage, CompanyPipelineStage, SubStatus }
