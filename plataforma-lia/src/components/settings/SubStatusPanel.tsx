"use client"

import React from "react"
import { Switch } from "@/components/ui/switch"
import { InteractiveSurface } from "@/components/ui/interactive-surface"
import { ChevronDown, ChevronRight, Star, Loader2 } from "lucide-react"
import { useTranslations } from "next-intl"
import { useSubStatusPanel } from "@/hooks/recruitment/use-sub-status-panel"
import { isRealId } from "./StageCardHelpers"
import type { RecruitmentStage } from "./recruitment-journey.types"

interface SubStatusPanelProps {
  stage: RecruitmentStage
  isEditMode: boolean
  onToggleSubStatus?: (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => Promise<void>
}

export function SubStatusPanel({ stage, isEditMode, onToggleSubStatus }: SubStatusPanelProps) {
  const t = useTranslations("settings.recruitment.pipeline.subStatus")
  const {
    expanded, displayList, loading, togglingId, activeCount, canFetch,
    handleExpand, handleToggleActive, handleToggleDefault,
  } = useSubStatusPanel({
    stageId: stage.id,
    initialSubStatuses: stage.sub_statuses || [],
    onToggleSubStatus,
  })

  const canManage = isEditMode && canFetch && !!onToggleSubStatus
  const stageName = stage.display_name || stage.name

  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle mt-3 pt-2">
      <InteractiveSurface
        variant="accordion"
        onClick={handleExpand}
        className="flex items-center gap-1.5 justify-start text-xs text-lia-text-secondary hover:text-lia-text-primary !bg-transparent hover:!bg-transparent"
        aria-expanded={expanded}
        aria-label={t("toggleAria", { action: expanded ? t("collapse") : t("expand"), name: stageName })}
        data-testid={`sub-status-panel-${stage.id}`}
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <span className="font-medium">{t("subStatusesLabel")}</span>
        <span className="text-lia-text-tertiary">{t("activeCount", { count: activeCount })}</span>
        {!isRealId(stage.id) && isEditMode && (
          <span className="ml-auto text-micro text-status-warning">{t("saveStageFirst")}</span>
        )}
      </InteractiveSurface>

      {expanded && (
        <div className="mt-2 space-y-1.5" role="status" aria-live="polite" aria-label={t("loading")}>
          {loading && (
            <div className="flex items-center gap-2 px-1 py-2" role="status" aria-live="polite" aria-label={t("loading")}>
              <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
              <span className="text-xs text-lia-text-tertiary">{t("loadingSubStatuses")}</span>
            </div>
          )}

          {!loading && displayList.length === 0 && (
            <p className="text-xs text-lia-text-tertiary px-1 py-1 italic">
              {t("noSubStatuses")}
            </p>
          )}

          {!loading && displayList.map(ss => (
            <div
              key={ss.id}
              className={`flex items-center gap-2 px-2 py-1.5 rounded-md border transition-colors motion-reduce:transition-none ${
                ss.is_active
                  ? 'bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-default'
                  : 'bg-lia-bg-secondary dark:bg-lia-bg-primary/50 border-lia-border-subtle dark:border-lia-border-subtle opacity-60'
              }`}
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{backgroundColor: ss.color || 'var(--lia-text-tertiary)'}}
              />
              <span className={`flex-1 text-xs font-medium ${ss.is_active ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>
                {ss.display_name}
              </span>

              {ss.is_waiting && ss.is_active && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan-text text-micro font-medium">
                  {t("waiting")}
                </span>
              )}

              {canManage && ss.is_active && (
                <button
                  onClick={() => handleToggleDefault(ss)}
                  disabled={togglingId === `default-${ss.id}`}
                  aria-label={ss.is_default ? t("removeDefault", { name: ss.display_name }) : t("setDefault", { name: ss.display_name })}
                  title={ss.is_default ? t("removeDefaultShort") : t("setDefaultShort")}
                  className="p-0.5 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-border-medium transition-colors motion-reduce:transition-none"
                  data-testid={`sub-status-default-toggle-${ss.id}`}
                  type="button"
                >
                  {togglingId === `default-${ss.id}` ? (
                    <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
                  ) : ss.is_default ? (
                    <Star className="h-3 w-3 text-status-warning fill-current" />
                  ) : (
                    <Star className="h-3 w-3 text-lia-text-disabled hover:text-status-warning" />
                  )}
                </button>
              )}

              {canManage && (
                <Switch
                  data-toggle="is_active"
                  data-testid={`sub-status-active-toggle-${ss.id}`}
                  checked={ss.is_active ?? true}
                  onCheckedChange={() => handleToggleActive(ss)}
                  disabled={togglingId === ss.id}
                  aria-label={t("toggleActive", { action: ss.is_active ? t("deactivate") : t("activate"), name: ss.display_name })}
                />
              )}

              {!canManage && ss.is_default && (
                <Star className="h-3 w-3 text-status-warning fill-current flex-shrink-0" />
              )}
            </div>
          ))}

          {canManage && displayList.length > 0 && (
            <p className="text-micro text-lia-text-tertiary px-1 pt-1">
              {t("manageHelp")}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
