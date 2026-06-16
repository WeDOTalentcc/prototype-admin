"use client"

import React, { useState, useEffect, useRef } from "react"
import { useTranslations } from "next-intl"
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor,
  useSensor, useSensors, DragEndEvent,
} from "@dnd-kit/core"
import {
  arrayMove, SortableContext, sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Plus, Lock, Shield, Settings, AlertTriangle, Loader2 } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { fetchWithRetry, HttpError } from "@/services/lia-api"
import {
  SortableStageCard, ReadOnlyStageCard,
  getActionBehaviorShort,
} from "./StageCard"
import type { SubStatus, RecruitmentStage, RecruitmentJourneyConfigProps } from "./recruitment-journey.types"
import { HubHeader } from "./_shared"

export type { SubStatus, RecruitmentStage, RecruitmentJourneyConfigProps }

// ---------------------------------------------------------------------------
// Types (local only)
// ---------------------------------------------------------------------------

interface CatalogStage {
  id: string
  name: string
  display_name: string
  color?: string
  icon?: string
  action_behavior?: string
  default_channel?: string
  stage_category?: string
  sla_hours?: number
  description?: string
}

// ---------------------------------------------------------------------------
// Default stages fallback
// ---------------------------------------------------------------------------

// NOTE: display_name values are canonical English fallbacks. The UI looks up
// a locale-specific label from `settings.recruitment.journey.defaultStageNames.<name>`
// at render time via `getStageDisplayName()`, so users see translated stage
// names in both pt-BR and EN.
// TODO P2-W1-01: DEFAULT_STAGES (15 itens) serve como fallback quando GET /stage-catalog falha.
// Se empresa nova nunca configurou pipeline, este array é legítimo como ponto de partida.
// Considerar reduzir para ~5 etapas essenciais (sourcing, screening, interview, offer, hired)
// e adicionar as demais via catalogo. Single source of truth: backend /api/v1/stage-catalog.
export const DEFAULT_STAGES: RecruitmentStage[] = [
  { id: "1",  name: "sourcing",            display_name: "Sourcing",           order: 1,  isActive: true, notes: "", sla: 0, type: "system",  color: "var(--lia-text-secondary)", icon: "search",      action_behavior: "intake",               default_channel: "email",         stage_category: "system"  },
  { id: "2",  name: "screening",           display_name: "Screening",          order: 2,  isActive: true, notes: "", sla: 0, type: "system",  color: "var(--wedo-purple)", icon: "file-text",   action_behavior: "screening",            default_channel: "email",         stage_category: "system"  },
  { id: "3",  name: "long_list",           display_name: "Long List",          order: 3,  isActive: true, notes: "", sla: 3, type: "custom",  color: "var(--lia-border-subtle)", icon: "list",        action_behavior: "passive",              default_channel: "email",         stage_category: "custom"  },
  { id: "4",  name: "short_list",          display_name: "Short List",         order: 4,  isActive: true, notes: "", sla: 3, type: "custom",  color: "var(--lia-border-subtle)", icon: "list-checks", action_behavior: "passive",              default_channel: "email",         stage_category: "custom"  },
  { id: "5",  name: "interview_hr",        display_name: "HR Interview",       order: 5,  isActive: true, notes: "", sla: 0, type: "system",  color: "var(--lia-text-tertiary)", icon: "users",       action_behavior: "scheduling",           default_channel: "email_whatsapp", stage_category: "system"  },
  { id: "6",  name: "technical_test",      display_name: "Technical Test",     order: 6,  isActive: true, notes: "", sla: 5, type: "custom",  color: "var(--lia-border-subtle)", icon: "code-2",      action_behavior: "evaluation",           default_channel: "email",         stage_category: "custom"  },
  { id: "7",  name: "english_test",        display_name: "English Test",       order: 7,  isActive: true, notes: "", sla: 5, type: "custom",  color: "var(--lia-border-subtle)", icon: "languages",   action_behavior: "evaluation",           default_channel: "email",         stage_category: "custom"  },
  { id: "8",  name: "interview_technical", display_name: "Technical Interview",order: 8,  isActive: true, notes: "", sla: 5, type: "custom",  color: "var(--status-warning)", icon: "code",        action_behavior: "scheduling",           default_channel: "email_whatsapp", stage_category: "custom"  },
  { id: "9",  name: "interview_manager",   display_name: "Manager Interview",  order: 9,  isActive: true, notes: "", sla: 5, type: "custom",  color: "var(--status-success)", icon: "briefcase",   action_behavior: "scheduling",           default_channel: "email_whatsapp", stage_category: "custom"  },
  { id: "10", name: "interview_final",     display_name: "Final Interview",    order: 10, isActive: true, notes: "", sla: 5, type: "custom",  color: "var(--lia-border-subtle)", icon: "award",       action_behavior: "scheduling",           default_channel: "email_whatsapp", stage_category: "custom"  },
  { id: "11", name: "references",          display_name: "References",         order: 11, isActive: true, notes: "", sla: 3, type: "custom",  color: "var(--lia-bg-tertiary)", icon: "phone",       action_behavior: "verification",         default_channel: "email",         stage_category: "custom"  },
  { id: "12", name: "offer",               display_name: "Offer",              order: 12, isActive: true, notes: "", sla: 3, type: "default", color: "var(--lia-text-secondary)", icon: "file-check",  action_behavior: "offer",                default_channel: "email",         stage_category: "catalog" },
  { id: "13", name: "offer_declined",      display_name: "Offer Declined",     order: 13, isActive: true, notes: "", sla: 0, type: "default", color: "var(--status-warning)", icon: "x",           action_behavior: "conclusion_declined",  default_channel: "email",         stage_category: "catalog" },
  { id: "14", name: "hired",               display_name: "Hired",              order: 14, isActive: true, notes: "", sla: 0, type: "system",  color: "var(--status-success)", icon: "check-circle",action_behavior: "conclusion_hired",     default_channel: "email",         stage_category: "system"  },
  { id: "15", name: "rejected",            display_name: "Rejected",           order: 15, isActive: true, notes: "", sla: 0, type: "system",  color: "var(--status-error)", icon: "x-circle",   action_behavior: "conclusion_rejected",  default_channel: "email",         stage_category: "system"  },
]

// Includes both canonical `name` keys and historical PT/EN display_name strings
// so the system-end split keeps working across legacy data and translations.
const SYSTEM_END_NAMES = ['hired', 'rejected', 'Contratado', 'Reprovado', 'Hired', 'Rejected']

function splitSystemEnd(stages: RecruitmentStage[]) {
  const end = stages.filter(s => s.type === 'system' && (SYSTEM_END_NAMES.includes(s.name) || SYSTEM_END_NAMES.includes(s.display_name)))
  const rest = stages.filter(s => !end.includes(s))
  return { end, rest }
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

// NOTE: action_behavior + default_channel propagate via onChange(stages) → saved on "Salvar".
// Sub-status toggle is auto-saved immediately via onToggleSubStatus callback.
export function RecruitmentJourneyConfig({
  stages,
  onChange,
  isEditMode = true,
  hideHeader = false,
  onToggleSubStatus,
}: RecruitmentJourneyConfigProps) {
  const t = useTranslations("settings.recruitment.journey")
  const [newlyAddedStageId, setNewlyAddedStageId] = useState<string | null>(null)
  const [catalogStages, setCatalogStages] = useState<CatalogStage[]>([])
  const [catalogOpen, setCatalogOpen] = useState(false)
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [catalogHasError, setCatalogHasError] = useState(false)
  const catalogError = catalogHasError ? t("catalogLoadError") : null
  const [catalogReloadKey, setCatalogReloadKey] = useState(0)
  const stageRefs = useRef<Map<string, HTMLDivElement>>(new Map())

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  useEffect(() => {
    const controller = new AbortController()
    let cancelled = false
    setCatalogLoading(true)
    setCatalogHasError(false)
    fetchWithRetry('/api/backend-proxy/stage-catalog', { signal: controller.signal }, { attempts: 2, timeoutMs: 15000 })
      .then(async (r) => {
        if (!r.ok) throw new HttpError(r.status, `HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        if (cancelled) return
        if (!data) return
        setCatalogStages(data.catalog ?? (Array.isArray(data) ? data : []))
      })
      .catch((err) => {
        if (cancelled) return
        if (err?.name === 'AbortError') return
        // Use console.warn — Next dev overlay only intercepts uncaught errors
        // and unhandled rejections; warn keeps the noise out of the overlay.
        console.warn('[RecruitmentJourneyConfig] stage-catalog fetch failed', err)
        setCatalogHasError(true)
      })
      .finally(() => {
        if (!cancelled) setCatalogLoading(false)
      })
    return () => {
      cancelled = true
      controller.abort()
    }
  }, [catalogReloadKey])

  useEffect(() => {
    if (!newlyAddedStageId) return
    const el = stageRefs.current.get(newlyAddedStageId)
    if (el) {
      setTimeout(() => {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        el.classList.add('ring-2', 'ring-lia-btn-primary-bg', 'dark:ring-lia-border-subtle', 'ring-offset-2')
        setTimeout(() => el.classList.remove('ring-2', 'ring-lia-btn-primary-bg', 'dark:ring-lia-border-subtle', 'ring-offset-2'), 2000)
      }, 100)
    }
    setNewlyAddedStageId(null)
  }, [newlyAddedStageId, stages])

  const handleDragEnd = (event: DragEndEvent) => {
    if (!isEditMode) return
    const { active, over } = event
    if (!over || active.id === over.id) return

    const activeStage = stages.find(s => s.id === active.id)
    const overStage = stages.find(s => s.id === over.id)
    if (activeStage?.type === 'system' || overStage?.type === 'system') return

    const oldIndex = stages.findIndex(s => s.id === active.id)
    const newIndex = stages.findIndex(s => s.id === over.id)

    const systemStartCount = stages.filter(s => s.type === 'system' && !SYSTEM_END_NAMES.includes(s.name) && !SYSTEM_END_NAMES.includes(s.display_name)).length
    const systemEndStartIndex = stages.length - stages.filter(s => s.type === 'system' && (SYSTEM_END_NAMES.includes(s.name) || SYSTEM_END_NAMES.includes(s.display_name))).length

    if (newIndex < systemStartCount || newIndex >= systemEndStartIndex) return

    onChange(arrayMove(stages, oldIndex, newIndex).map((s, i) => ({ ...s, order: i + 1 })))
  }

  const handleUpdate = (id: string, updates: Partial<RecruitmentStage>) => {
    if (!isEditMode) return
    const stage = stages.find(s => s.id === id)

    if (stage?.type === 'system') {
      const allowed = new Set(['sla', 'action_behavior', 'default_channel'])
      const safe = Object.fromEntries(Object.entries(updates).filter(([k]) => allowed.has(k)))
      if (!Object.keys(safe).length) return
      onChange(stages.map(s => s.id === id ? { ...s, ...safe } : s))
      return
    }

    onChange(stages.map(s => s.id === id ? { ...s, ...updates } : s))
  }

  const handleRemove = (id: string) => {
    if (!isEditMode) return
    if (stages.find(s => s.id === id)?.type !== 'custom') return
    onChange(stages.filter(s => s.id !== id).map((s, i) => ({ ...s, order: i + 1 })))
  }

  const handleAddStage = () => {
    if (!isEditMode) return
    const newId = `stage-${Date.now()}`
    const { end, rest } = splitSystemEnd(stages)
    const newStage: RecruitmentStage = {
      id: newId, name: `custom_${Date.now()}`, display_name: t("newStage"),
      order: rest.length + 1, isActive: true, notes: "", sla: 3,
      type: "custom", action_behavior: "passive", stage_category: "custom",
    }
    onChange([...rest, newStage, ...end].map((s, i) => ({ ...s, order: i + 1 })))
    setNewlyAddedStageId(newId)
    setCatalogOpen(false)
  }

  const handleAddFromCatalog = (cs: CatalogStage) => {
    if (!isEditMode) return
    const newId = `catalog-${Date.now()}`
    const { end, rest } = splitSystemEnd(stages)
    const newStage: RecruitmentStage = {
      id: newId, name: cs.name, display_name: cs.display_name,
      order: rest.length + 1, isActive: true, notes: cs.description || "",
      sla: cs.sla_hours ? Math.round(cs.sla_hours / 24) : 3,
      type: cs.stage_category === 'system' ? 'system' : (cs.stage_category === 'catalog' ? 'default' : 'custom'),
      color: cs.color, icon: cs.icon,
      action_behavior: cs.action_behavior || 'passive',
      default_channel: cs.default_channel || 'email',
      stage_category: cs.stage_category, catalog_id: cs.id,
    }
    onChange([...rest, newStage, ...end].map((s, i) => ({ ...s, order: i + 1 })))
    setNewlyAddedStageId(newId)
    setCatalogOpen(false)
  }

  const availableCatalogStages = catalogStages.filter(cs => !stages.some(s => s.name === cs.name))

  return (
    <div className="space-y-4" data-testid="pipeline-journey-root">
      {!hideHeader && (
        <HubHeader title={t("title")} description={isEditMode ? t("descEdit") : t("descView")}>
          {isEditMode && (
            <Popover open={catalogOpen} onOpenChange={setCatalogOpen}>
              <PopoverTrigger asChild>
                <Button data-testid="pipeline-stage-add-trigger" className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active px-4 py-2 text-xs font-semibold transition-colors motion-reduce:transition-none">
                  <Plus className="h-4 w-4 mr-2" />
                  {t("addStage")}
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end" className="w-80 p-0" data-testid="pipeline-stage-catalog-popover">
                <div className="p-3 dark:border-lia-border-subtle">
                  <h4 className={`${textStyles.bodyLarge} font-semibold text-lia-text-primary`}>
                    {t("addFromCatalog")}
                  </h4>
                </div>
                <div className="max-h-64 overflow-y-auto p-2">
                  {catalogLoading && catalogStages.length === 0 ? (
                    <div className="flex items-center gap-2 px-3 py-4 text-lia-text-tertiary">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className={textStyles.description}>{t("loadingCatalog")}</span>
                    </div>
                  ) : catalogError && catalogStages.length === 0 ? (
                    <div className="px-3 py-4 space-y-2">
                      <div className="flex items-start gap-2 text-status-warning">
                        <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                        <p className={`${textStyles.description} text-status-warning`}>{catalogError}</p>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setCatalogReloadKey((k) => k + 1)}
                        className="w-full"
                      >
                        {t("retry")}
                      </Button>
                    </div>
                  ) : availableCatalogStages.length > 0 ? (
                    availableCatalogStages.map(cs => (
                      <button
                        key={cs.id}
                        data-testid={`pipeline-catalog-add-${cs.name}`}
                        onClick={() => handleAddFromCatalog(cs)}
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50 transition-colors motion-reduce:transition-none text-left"
                      >
                        <span className="w-3 h-3 rounded-full flex-shrink-0" style={{backgroundColor: cs.color || 'var(--lia-text-tertiary)'}} />
                        <span className={`flex-1 ${textStyles.body} text-lia-text-primary`}>{cs.display_name}</span>
                        {cs.action_behavior && (
                          <span className="text-micro text-lia-text-tertiary">{getActionBehaviorShort(cs.action_behavior)}</span>
                        )}
                      </button>
                    ))
                  ) : (
                    <p className={`px-3 py-2 ${textStyles.description}`}>
                      {t("allCatalogAdded")}
                    </p>
                  )}
                </div>
                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-2">
                  <button
                    data-testid="pipeline-stage-create-custom"
                    onClick={handleAddStage}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50 transition-colors motion-reduce:transition-none text-left"
                  >
                    <Plus className="h-4 w-4 text-lia-text-secondary" />
                    <span className={`${textStyles.body} text-lia-text-secondary`}>{t("createCustom")}</span>
                  </button>
                </div>
              </PopoverContent>
            </Popover>
          )}
        </HubHeader>
      )}

      <div className="mb-4 p-3 bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-strong">
        <div className={`flex items-center gap-4 flex-wrap ${textStyles.caption}`}>
          <div className="flex items-center gap-1">
            <Lock className="h-3 w-3 text-lia-text-tertiary" />
            <span><strong>{t("systemLabel")}</strong> {t("systemDesc")}</span>
          </div>
          <div className="flex items-center gap-1">
            <Shield className="h-3 w-3 text-wedo-cyan-dark dark:text-wedo-cyan-dark" />
            <span><strong>{t("defaultLabel")}</strong> {t("defaultDesc")}</span>
          </div>
          <div className="flex items-center gap-1">
            <Settings className="h-3 w-3 text-wedo-purple" />
            <span><strong>{t("customLabel")}</strong> {t("customDesc")}</span>
          </div>
        </div>
      </div>

      {isEditMode ? (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={stages.map(s => s.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-3" data-testid="pipeline-stages-list-edit">
              {stages.map(stage => (
                <SortableStageCard
                  key={stage.id}
                  stage={stage}
                  onUpdate={handleUpdate}
                  onRemove={handleRemove}
                  onToggleSubStatus={onToggleSubStatus}
                  isEditMode={true}
                  registerRef={(id, el) => {
                    if (el) stageRefs.current.set(id, el)
                    else stageRefs.current.delete(id)
                  }}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      ) : (
        <div className="space-y-3" data-testid="pipeline-stages-list-readonly">
          {stages.map(stage => <ReadOnlyStageCard key={stage.id} stage={stage} />)}
        </div>
      )}

      {stages.length === 0 && (
        <div className="text-center py-12 bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl border-2 border-dashed border-lia-border-subtle dark:border-lia-border-subtle">
          <p className={textStyles.bodyLarge}>
            {t("noStages")} {isEditMode && t("noStagesHint")}
          </p>
        </div>
      )}
    </div>
  )
}

export default RecruitmentJourneyConfig
