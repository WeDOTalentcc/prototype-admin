"use client"

import { useCallback } from 'react'
import type {
  CommunicationTemplate,
  TemplateSituation,
  TemplateChannel,
} from './communication-templates-types'

export interface UseTemplateEditorReturn {
  getTemplatesBySituation: (situation: TemplateSituation) => CommunicationTemplate[]
  getTemplatesByChannel: (channel: TemplateChannel) => CommunicationTemplate[]
}

/**
 * Provides filtering helpers over a template list.
 * Operates on the templates array passed in (typically from useTemplateList).
 */
export function useTemplateEditor(templates: CommunicationTemplate[]): UseTemplateEditorReturn {
  const getTemplatesBySituation = useCallback(
    (sit: TemplateSituation): CommunicationTemplate[] => {
      return templates.filter(t => t.situation === sit && t.isActive)
    },
    [templates]
  )

  const getTemplatesByChannel = useCallback(
    (ch: TemplateChannel): CommunicationTemplate[] => {
      return templates.filter(t => t.channel === ch && t.isActive)
    },
    [templates]
  )

  return {
    getTemplatesBySituation,
    getTemplatesByChannel,
  }
}
