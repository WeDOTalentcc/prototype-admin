"use client"

import { useCallback } from "react"
import { type DynamicStage } from "@/components/kanban"
import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"

interface UseKanbanColumnConfigProps {
  dynamicStages: DynamicStage[]
}

export function useKanbanColumnConfig({ dynamicStages }: UseKanbanColumnConfigProps) {
  // Canonical pipeline da empresa via /api/backend-proxy/company-pipeline.
  // Substitui o lookup hardcoded em RECRUITMENT_STAGES (mantido como fallback
  // transitional quando o backend ainda nao respondeu OU empresa nao configurou).
  // WT-2022 P0.STAGES: stages tem shape canonical (snake_case);
  // legacyStages tem shape camelCase (drop-in p/ utils legacy).
  const { stages: companyPipelineStages, legacyStages: companyPipelineLegacy } =
    useRecruitmentStages()
  const getColumnStyle = (columnId: string) => {
    // Estilos fixos para etapas conhecidas
    const fixedStyles: Record<string, { bg: string; border: string; dot: string; header: string; accentColor: string }> = {
      sourcing: {
        bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-lia-bg-inverse dark:bg-lia-border-default',
        header: 'text-lia-text-primary',
        accentColor: 'var(--lia-text-secondary)'
      },
      hired: {
        bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-lia-bg-inverse dark:bg-lia-border-default',
        header: 'text-lia-text-primary',
        accentColor: 'var(--lia-text-secondary)'
      },
      rejected: {
        bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-lia-border-default dark:bg-lia-bg-elevated',
        header: 'text-lia-text-primary',
        accentColor: 'var(--lia-border-subtle)'
      },
      offer_declined: {
        bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-lia-border-default dark:bg-lia-bg-elevated',
        header: 'text-lia-text-primary',
        accentColor: 'var(--lia-border-subtle)'
      }
    }

    if (fixedStyles[columnId]) {
      return fixedStyles[columnId]
    }

    // Para etapas dinâmicas, buscar a cor da etapa
    const dynamicStage = dynamicStages.find(s => s.id === columnId)
    const stageColor = dynamicStage?.color || 'var(--lia-text-tertiary)'

    return {
      bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
      border: 'border-lia-border-subtle dark:border-lia-border-subtle',
      dot: 'bg-lia-bg-secondary0 dark:bg-lia-border-medium',
      header: 'text-lia-text-primary',
      accentColor: stageColor
    }
  }

  const getStageAccentStyle = (stage: string) => {
    const style = getColumnStyle(stage)
    return {
      backgroundColor: style.accentColor,
      borderColor: style.accentColor
    }
  }

  const getStageCategory = useCallback((stage: DynamicStage): 'system' | 'default' | 'custom' => {
    if (stage.isInitial || stage.isFinal || stage.isHired || stage.isRejection) return 'system'
    const systemIds = ['sourcing', 'screening', 'hired', 'rejected', 'offer_declined']
    if (systemIds.includes(stage.id)) return 'system'
    const defaultIds = ['long_list', 'short_list', 'interview_hr', 'technical_test', 'english_test',
      'interview_technical', 'interview_manager', 'interview_final', 'references', 'offer',
      'entrevista_rh', 'teste_tecnico', 'teste_de_ingles', 'entrevista_tecnica', 'entrevista_gestor',
      'entrevista_final', 'referencias', 'proposta']
    if (defaultIds.includes(stage.id)) return 'default'
    return 'custom'
  }, [])

  const getStageDisplayName = (stageId: string): string => {
    const stage = dynamicStages.find(s => s.id === stageId)
    if (stage) return stage.displayName
    // Canonical: usar pipeline da empresa (Configuracoes > Pipeline).
    const companyStage = companyPipelineStages.find(s => s.name === stageId)
    if (companyStage?.display_name) return companyStage.display_name
    // WT-2022 P0.STAGES (pattern example): legacyStages do hook expoe
    // shape camelCase (mesmo dataset que companyPipelineStages). Util pra
    // utils legacy que esperam displayName/stageOrder/stageType/isInitial/
    // isFinal/stageCategory/allowedTransitions. Aqui ainda eh redundante
    // com a linha anterior (display_name == displayName), mas demonstra
    // o pattern p/ outros consumers que dependem dos demais fields.
    const recruitmentStageLegacy = companyPipelineLegacy.find(s => s.name === stageId)
    return recruitmentStageLegacy?.displayName || stageId
  }

  const STAGE_PASTEL_COLORS: Record<string, string> = {
    'sourcing': 'var(--lia-border-subtle)',
    'screening': 'var(--lia-border-subtle)',
    'interview_hr': 'var(--lia-border-default)',
    'interview_technical': 'var(--lia-border-default)',
    'interview_manager': 'var(--lia-border-default)',
    'offer': 'var(--lia-border-default)',
    'hired': 'var(--lia-border-default)',
    'rejected': 'var(--lia-border-default)',
    'offer_declined': 'var(--lia-border-default)'
  }

  return {
    getColumnStyle,
    getStageAccentStyle,
    getStageCategory,
    getStageDisplayName,
    STAGE_PASTEL_COLORS,
  }
}
