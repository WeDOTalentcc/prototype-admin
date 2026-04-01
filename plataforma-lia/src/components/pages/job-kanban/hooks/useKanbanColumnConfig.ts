"use client"

import { useCallback } from "react"
import { type DynamicStage } from "@/components/kanban"
import { RECRUITMENT_STAGES } from "@/lib/recruitment-stages"

interface UseKanbanColumnConfigProps {
  dynamicStages: DynamicStage[]
}

export function useKanbanColumnConfig({ dynamicStages }: UseKanbanColumnConfigProps) {
  const getColumnStyle = (columnId: string) => {
    // Estilos fixos para etapas conhecidas
    const fixedStyles: Record<string, { bg: string; border: string; dot: string; header: string; accentColor: string }> = {
      sourcing: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-700 dark:bg-gray-300',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
        accentColor: 'var(--gray-600)'
      },
      hired: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-700 dark:bg-gray-300',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
        accentColor: 'var(--gray-600)'
      },
      rejected: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-300 dark:bg-lia-bg-elevated',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
        accentColor: 'var(--gray-200)'
      },
      offer_declined: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-300 dark:bg-lia-bg-elevated',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
        accentColor: 'var(--gray-200)'
      }
    }

    if (fixedStyles[columnId]) {
      return fixedStyles[columnId]
    }

    // Para etapas dinâmicas, buscar a cor da etapa
    const dynamicStage = dynamicStages.find(s => s.id === columnId)
    const stageColor = dynamicStage?.color || 'var(--gray-400)'

    return {
      bg: 'bg-white dark:bg-lia-bg-primary',
      border: 'border-lia-border-subtle dark:border-lia-border-subtle',
      dot: 'bg-gray-500 dark:bg-gray-400',
      header: 'text-lia-text-primary dark:text-lia-text-primary',
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
    const recruitmentStage = RECRUITMENT_STAGES.find(s => s.name === stageId)
    return recruitmentStage?.displayName || stageId
  }

  const STAGE_PASTEL_COLORS: Record<string, string> = {
    'sourcing': 'var(--gray-200)',
    'screening': 'var(--gray-200)',
    'interview_hr': 'var(--gray-300)',
    'interview_technical': 'var(--gray-300)',
    'interview_manager': 'var(--gray-300)',
    'offer': 'var(--gray-300)',
    'hired': 'var(--gray-300)',
    'rejected': 'var(--gray-300)',
    'offer_declined': 'var(--gray-300)'
  }

  return {
    getColumnStyle,
    getStageAccentStyle,
    getStageCategory,
    getStageDisplayName,
    STAGE_PASTEL_COLORS,
  }
}
