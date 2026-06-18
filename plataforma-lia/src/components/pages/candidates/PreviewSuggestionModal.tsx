"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useEffect } from"react"
import { useTranslations } from "next-intl"
import { Brain, X, Plus, Loader2, Edit, Bookmark, Search } from"lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from"@/components/ui/dialog"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { toast } from"sonner"
import type { ModalAISuggestion, ModalArchetype } from"./CandidatesPageModals.types"
import type { Archetype } from"./hooks/useCandidatesArchetypes"

interface ArchetypeUpdate {
  name: string
  description: string
  query: string
  filters: Record<string, string[]>
  tags: string[]
}

interface PreviewSuggestionModalProps {
  previewSuggestion: ModalAISuggestion | null
  previewingUserArchetype: ModalArchetype | null
  onClose: () => void
  buildFiltersFromTags: (tags: string[]) => Record<string, string[]>
  onUpdateArchetype: (id: string, updates: ArchetypeUpdate) => void
  onSaveArchetype: (newArchetype: ModalArchetype) => void
  onExecuteSearch: (query: string, filters: Record<string, string[]>, mode: string, metadata: { mode: string }, reset: boolean) => Promise<void>
  onSetLiaPromptValue: (value: string) => void
  onSetActiveSearchTab: (tab: string) => void
}

export function PreviewSuggestionModal({
  previewSuggestion,
  previewingUserArchetype,
  onClose,
  buildFiltersFromTags,
  onUpdateArchetype,
  onSaveArchetype,
  onExecuteSearch,
  onSetLiaPromptValue,
  onSetActiveSearchTab,
}: PreviewSuggestionModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('preview-suggestion', previewSuggestion)

  const t = useTranslations('candidates.modals')
const [previewTags, setPreviewTags] = useState<string[]>([])
  const [newPreviewTag, setNewPreviewTag] = useState("")
  const [isSavingPreviewArchetype, setIsSavingPreviewArchetype] = useState(false)

  useEffect(() => {
    if (previewSuggestion) {
      setPreviewTags([])
      setNewPreviewTag("")
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previewSuggestion?.name])

  return (
    <Dialog open={!!previewSuggestion} onOpenChange={(open) => {
      if (!open) onClose()
    }}>
      <DialogContent className="max-w-md" data-testid="preview-suggestion-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary">
            <Brain className="w-5 h-5 text-wedo-cyan" />
            {previewSuggestion?.name}
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-tertiary">
            {previewSuggestion?.description}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div>
            <label className="text-xs font-medium mb-2 block">
              {t('searchCriteria')}
            </label>
            <div className="flex flex-wrap gap-2">
              {previewTags.map((tag, index) => (
                <Chip variant="neutral" muted
                  key={`tag-${index}`}
                  className="!text-xs !px-2 !py-1 flex items-center gap-1.5"
                 
                >
                  {tag}
                  <button
                    onClick={() => setPreviewTags(prev => prev.filter((_, i) => i !== index))}
                    className="ml-0.5 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse rounded-full p-0.5 transition-colors motion-reduce:transition-none"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Chip>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-medium mb-2 block">
              {t('addCriteria')}
            </label>
            <div className="flex gap-2">
              <Input
                value={newPreviewTag}
                onChange={(e) => setNewPreviewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && newPreviewTag.trim()) {
                    e.preventDefault()
                    setPreviewTags(prev => [...prev, newPreviewTag.trim()])
                    setNewPreviewTag("")
                  }
                }}
                placeholder={t('typeAndPressEnter')}
                className="text-sm"
              />
              <Button
                type="button"
                size="sm"
                onClick={() => {
                  if (newPreviewTag.trim()) {
                    setPreviewTags(prev => [...prev, newPreviewTag.trim()])
                    setNewPreviewTag("")
                  }
                }}
                className="bg-lia-btn-primary-bg"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2 sm:gap-3 pt-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="w-full sm:w-auto order-3 sm:order-1"
          >
            {t('cancel')}
          </Button>
          <Button
            variant="outline"
            onClick={async () => {
              if (!previewSuggestion) return
              if (previewTags.length === 0) {
                toast.error(t('noCriteria'), { description: t('addAtLeastOneCriteriaSave') })
                return
              }
              setIsSavingPreviewArchetype(true)
              try {
                const editedFilters = buildFiltersFromTags(previewTags)
                const queryFromTags = previewTags.join(' ')

                if (previewingUserArchetype) {
                  const response = await fetch(`/api/backend-proxy/search/archetypes/${previewingUserArchetype.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      name: previewSuggestion.name,
                      description: previewSuggestion.description,
                      query: queryFromTags,
                      criteria: {
                        keywords: editedFilters.keywords,
                        skills: editedFilters.skills,
                        locations: editedFilters.locations,
                        seniority: editedFilters.seniority
                      },
                    }),
                  })

                  if (!response.ok && response.status !== 404) {
                    throw new Error(`Failed to update archetype: ${response.status}`)
                  }

                  onUpdateArchetype(previewingUserArchetype.id, {
                    name: previewSuggestion.name,
                    description: previewSuggestion.description,
                    query: queryFromTags,
                    filters: editedFilters,
                    tags: previewTags,
                  })
                  toast.success(t('archetypeUpdated'), { description: t('archetypeUpdatedDescription', { name: previewSuggestion.name }) })
                } else {
                  const response = await fetch('/api/backend-proxy/search/archetypes/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      name: previewSuggestion.name,
                      description: previewSuggestion.description,
                      query: queryFromTags,
                      criteria: {
                        keywords: editedFilters.keywords,
                        skills: editedFilters.skills,
                        locations: editedFilters.locations,
                        seniority: editedFilters.seniority
                      },
                      emoji: '✨',
                    }),
                  })

                  if (!response.ok) {
                    throw new Error(`Failed to save archetype: ${response.status}`)
                  }

                  const savedArchetype = await response.json()
                  const newArchetype: Archetype = {
                    id: savedArchetype.id || `arch-${Date.now()}`,
                    name: previewSuggestion.name,
                    description: previewSuggestion.description,
                    emoji: '✨',
                    query: queryFromTags,
                    filters: editedFilters,
                    tags: previewTags,
                    createdAt: new Date()
                  }
                  onSaveArchetype(newArchetype)
                  toast.success(t('archetypeSaved'), { description: t('archetypeSavedDescription', { name: previewSuggestion.name }) })
                }
                onClose()
              } catch {
                toast.error(t('saveError'), { description: t('saveErrorDescription') })
              } finally {
                setIsSavingPreviewArchetype(false)
              }
            }}
            disabled={isSavingPreviewArchetype || previewTags.length === 0}
            className="w-full sm:w-auto order-2"
          >
            {isSavingPreviewArchetype ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                {previewingUserArchetype ? t('updating') : t('saving')}
              </>
            ) : previewingUserArchetype ? (
              <>
                <Edit className="w-4 h-4 mr-2" />
                {t('updateArchetype')}
              </>
            ) : (
              <>
                <Bookmark className="w-4 h-4 mr-2" />
                {t('saveAsMyArchetype')}
              </>
            )}
          </Button>
          <Button
            onClick={async () => {
              if (!previewSuggestion) return
              if (previewTags.length === 0) {
                toast.error(t('noCriteria'), { description: t('addAtLeastOneCriteriaExecute') })
                return
              }
              const editedFilters = buildFiltersFromTags(previewTags)
              const queryFromTags = previewTags.join(' ')
              onSetLiaPromptValue(queryFromTags)
              onSetActiveSearchTab('ia-natural')
              onClose()
              await onExecuteSearch(queryFromTags, editedFilters, 'natural', { mode: 'natural' }, false)
            }}
            disabled={previewTags.length === 0}
            className="w-full sm:w-auto order-1 sm:order-3 bg-lia-btn-primary-bg"
          >
            <Search className="w-4 h-4 mr-2" />
            {t('useSearch')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
