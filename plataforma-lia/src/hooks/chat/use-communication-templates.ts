"use client"

/**
 * useCommunicationTemplates — Facade hook.
 *
 * Composes useTemplateList, useTemplateEditor, and useTemplateSend into the
 * original combined interface so existing consumers need zero changes.
 */

// Re-export all public types from the shared types module
export type {
  TemplateChannel,
  TemplateSituation,
  CommunicationTemplate,
} from './communication-templates-types'
export { DEFAULT_TEMPLATES } from './communication-templates-types'

// Re-export sub-hooks for direct use
export { useTemplateList } from './useTemplateList'
export { useTemplateEditor } from './useTemplateEditor'
export { useTemplateSend } from './useTemplateSend'

import type {
  CommunicationTemplate,
  TemplateChannel,
  TemplateSituation,
} from './communication-templates-types'
import { useTemplateList } from './useTemplateList'
import { useTemplateEditor } from './useTemplateEditor'

interface UseCommunicationTemplatesOptions {
  channel?: TemplateChannel
  situation?: TemplateSituation
  autoLoad?: boolean
}

interface UseCommunicationTemplatesReturn {
  templates: CommunicationTemplate[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  getTemplatesBySituation: (situation: TemplateSituation) => CommunicationTemplate[]
  getTemplatesByChannel: (channel: TemplateChannel) => CommunicationTemplate[]
}

export function useCommunicationTemplates(
  options: UseCommunicationTemplatesOptions = {}
): UseCommunicationTemplatesReturn {
  const { channel, situation, autoLoad = true } = options

  const { templates: allTemplates, loading, error, refetch } = useTemplateList({ channel, autoLoad })
  const { getTemplatesBySituation, getTemplatesByChannel } = useTemplateEditor(allTemplates)

  return {
    templates: situation ? allTemplates.filter(t => t.situation === situation) : allTemplates,
    loading,
    error,
    refetch,
    getTemplatesBySituation,
    getTemplatesByChannel,
  }
}
