"use client"

import { useState, useEffect, useCallback } from 'react'
import type {
  CommunicationTemplate,
  TemplateChannel,
} from './communication-templates-types'
import { DEFAULT_TEMPLATES } from './communication-templates-types'

interface UseTemplateListOptions {
  channel?: TemplateChannel
  autoLoad?: boolean
}

export interface UseTemplateListReturn {
  templates: CommunicationTemplate[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useTemplateList(options: UseTemplateListOptions = {}): UseTemplateListReturn {
  const { channel, autoLoad = true } = options

  const [templates, setTemplates] = useState<CommunicationTemplate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (channel) params.set('channel', channel)

      const queryString = params.toString()
      const url = `/api/backend-proxy/email-templates${queryString ? `?${queryString}` : ''}`

      const response = await fetch(url)

      if (response.ok) {
        const result = await response.json()
        const templatesArray = result.items || (Array.isArray(result) ? result : [])

        const mappedTemplates: CommunicationTemplate[] = templatesArray.map((t: Record<string, unknown>) => ({
          id: t.id,
          name: t.name,
          category: t.category || 'followup',
          subject: t.subject || '',
          body: t.body || t.body_text || (t.body_html ? stripHtmlTags(t.body_html as string) : ''),
          variables: t.variables || [],
          isActive: t.is_active ?? true,
          lastUpdated: t.updated_at || t.last_updated || new Date().toISOString().split('T')[0],
          channel: t.channel || 'email',
          situation: t.situation || ''
        }))

        if (mappedTemplates.length > 0) {
          setTemplates(mappedTemplates)
        } else {
          const filteredDefaults = channel
            ? DEFAULT_TEMPLATES.filter(t => t.channel === channel)
            : DEFAULT_TEMPLATES
          setTemplates(filteredDefaults)
        }
      } else {
        const filteredDefaults = channel
          ? DEFAULT_TEMPLATES.filter(t => t.channel === channel)
          : DEFAULT_TEMPLATES
        setTemplates(filteredDefaults)
      }
    } catch (err) {
      setError('Erro ao carregar templates')
      const filteredDefaults = channel
        ? DEFAULT_TEMPLATES.filter(t => t.channel === channel)
        : DEFAULT_TEMPLATES
      setTemplates(filteredDefaults)
    } finally {
      setLoading(false)
    }
  }, [channel])

  useEffect(() => {
    if (autoLoad) {
      fetchTemplates()
    }
  }, [autoLoad, fetchTemplates])

  return {
    templates,
    loading,
    error,
    refetch: fetchTemplates,
  }
}

function stripHtmlTags(html: string): string {
  if (!html) return ''
  const isHtml = /<[a-z][\s\S]*>/i.test(html)
  if (!isHtml) return html

  const text = html
    .replace(/{{#if\s+\w+}}/gi, '')
    .replace(/{{\/if}}/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<p[^>]*>/gi, '')
    .replace(/<\/div>/gi, '\n')
    .replace(/<div[^>]*>/gi, '')
    .replace(/<\/li>/gi, '\n')
    .replace(/<li[^>]*>/gi, '\u2022 ')
    .replace(/<\/ul>/gi, '\n')
    .replace(/<ul[^>]*>/gi, '')
    .replace(/<\/ol>/gi, '\n')
    .replace(/<ol[^>]*>/gi, '')
    .replace(/<\/h[1-6]>/gi, '\n\n')
    .replace(/<h[1-6][^>]*>/gi, '')
    .replace(/<\/?(strong|b)[^>]*>/gi, '')
    .replace(/<\/?(em|i)[^>]*>/gi, '')
    .replace(/<a[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/gi, '$2')
    .replace(/<img[^>]*alt="([^"]*)"[^>]*\/?>/gi, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&rsquo;/g, "'")
    .replace(/&lsquo;/g, "'")
    .replace(/&rdquo;/g, '\u201c')
    .replace(/&ldquo;/g, '\u201d')
    .replace(/&mdash;/g, '\u2014')
    .replace(/&ndash;/g, '\u2013')
    .replace(/&#\d+;/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n /g, '\n')
    .replace(/ \n/g, '\n')
    .trim()

  return text
}
