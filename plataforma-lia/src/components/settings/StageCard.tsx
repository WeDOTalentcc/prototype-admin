"use client"

import React from "react"
import {
  useSortable,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { useTranslations } from "next-intl"
import { Card } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  GripVertical, Trash2, Check, X, Lock, Clock, Star,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import type { RecruitmentStage } from "./recruitment-journey.types"

export {
  getTypeBadge,
  getActionBehaviorLabel,
  getActionBehaviorShort,
  ActionBehaviorBadge,
  getStageDisplayName,
  useStageDisplayName,
  isRealId,
} from "./StageCardHelpers"

import {
  getTypeBadge,
  ActionBehaviorBadge,
  useStageDisplayName,
} from "./StageCardHelpers"
import { SubStatusPanel } from "./SubStatusPanel"
import { DataFieldsPanel } from "./DataFieldsPanel"
import { SaturationControlPanel } from "./SaturationControlPanel"

export function ReadOnlyStageCard({ stage }: { stage: RecruitmentStage }) {
  const t = useTranslations("settings.recruitment.pipeline.stage")
  const getStageDisplayName = useStageDisplayName()
  const isSystemStage = stage.type === 'system'

  const channelLabel = (channel: string) =>
    channel === 'whatsapp' ? t('channelWhatsapp') : t('channelEmailWhatsapp')

  return (
    <Card
      data-testid={`pipeline-stage-readonly-${stage.name}`}
      className={`border rounded-md p-4 bg-lia-bg-primary dark:bg-lia-bg-primary ${!stage.isActive ? "opacity-60" : ""} ${isSystemStage ? "border-lia-border-default bg-lia-bg-secondary/50" : "border-lia-border-subtle"}`}
      style={{borderLeft: stage.color ? `4px solid ${stage.color}` : undefined}}
    >
      <div className="flex items-start gap-3">
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-medium ${isSystemStage ? "bg-lia-interactive-active text-lia-text-secondary" : "bg-lia-bg-tertiary text-lia-text-secondary"}`}>
          {isSystemStage ? <Lock className="h-4 w-4" /> : stage.order}
        </div>

        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`flex-1 ${textStyles.bodyLarge} font-medium`}>
              {getStageDisplayName(stage)}
            </span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {getTypeBadge(stage.type)}
              <ActionBehaviorBadge behavior={stage.action_behavior} />
              {stage.isActive ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-status-success/10 text-status-success text-micro font-medium">
                  <Check className="h-3 w-3" />{t('active')}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-lia-bg-tertiary text-lia-text-secondary text-micro font-medium">
                  <X className="h-3 w-3" />{t('inactive')}
                </span>
              )}
            </div>
          </div>

          {stage.notes && <p className={`${textStyles.description} italic`}>{stage.notes}</p>}

          {stage.sla > 0 && (
            <div className="flex items-center gap-1.5 pt-1">
              <Clock className="h-3.5 w-3.5 text-lia-text-secondary" />
              <span className={textStyles.caption}>{t('sla')}: {stage.sla} {stage.sla === 1 ? t('slaDay') : t('slaDays')}</span>
            </div>
          )}

          {stage.default_channel && stage.default_channel !== 'email' && (
            <div className="flex items-center gap-1.5 pt-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
                {t('channelPrefix')} {channelLabel(stage.default_channel)}
              </span>
            </div>
          )}

          {(stage.sub_statuses?.length ?? 0) > 0 && (
            <div className="flex items-center gap-1 flex-wrap mt-1">
              {stage.sub_statuses?.map(ss => (
                <span key={ss.id} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-micro bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-elevated">
                  {ss.display_name}
                  {ss.is_default && <Star className="h-2.5 w-2.5 text-status-warning" />}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

export interface SortableStageCardProps {
  stage: RecruitmentStage
  onUpdate: (id: string, updates: Partial<RecruitmentStage>) => void
  onRemove: (id: string) => void
  onToggleSubStatus?: (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => Promise<void>
  isEditMode: boolean
  registerRef?: (id: string, element: HTMLDivElement | null) => void
}

export function SortableStageCard({
  stage, onUpdate, onRemove,
  onToggleSubStatus,
  isEditMode, registerRef,
}: SortableStageCardProps) {
  const t = useTranslations("settings.recruitment.pipeline.stage")
  const getStageDisplayName = useStageDisplayName()
  const isSystemStage = stage.type === 'system'
  const canEditName = !isSystemStage
  const canRemove = stage.type === 'custom'
  const canDrag = !isSystemStage

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: stage.id, disabled: !isEditMode || !canDrag })

  const style = { transform: CSS.Transform.toString(transform), transition }

  const combinedRef = (element: HTMLDivElement | null) => {
    setNodeRef(element)
    if (registerRef) registerRef(stage.id, element)
  }

  if (!isEditMode) return <ReadOnlyStageCard stage={stage} />

  return (
    <div ref={combinedRef} style={style} data-testid={`pipeline-stage-card-${stage.name}`}>
      <Card
        className={`border rounded-md p-4 transition-colors motion-reduce:transition-none duration-200 ${
          isDragging ? "opacity-90 bg-lia-bg-secondary" : "bg-lia-bg-primary hover:border-lia-border-medium dark:bg-lia-bg-secondary dark:hover:border-lia-border-medium"
        } ${!stage.isActive ? "opacity-60" : ""} ${
          isSystemStage ? "border-lia-border-default bg-lia-bg-secondary/50 dark:bg-lia-bg-primary/50" : "border-lia-border-subtle dark:border-lia-border-subtle"
        }`}
        style={{borderLeft: stage.color ? `4px solid ${stage.color}` : undefined}}
      >
        <div className="flex items-start gap-3">
          {canDrag ? (
            <button
              {...attributes} {...listeners}
              className="mt-1 cursor-grab active:cursor-grabbing p-1 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none"
              aria-label={t('dragToReorder')}
            >
              <GripVertical className="h-5 w-5 text-lia-text-tertiary" />
            </button>
          ) : (
            <div className="mt-1 p-1"><Lock className="h-5 w-5 text-lia-text-disabled" /></div>
          )}

          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-3 flex-wrap">
              {canEditName ? (
                <input
                  type="text"
                  data-field="display_name"
                  data-testid={`pipeline-stage-display-name-${stage.name}`}
                  value={getStageDisplayName(stage)}
                  onChange={(e) => onUpdate(stage.id, { display_name: e.target.value, name: stage.name })}
                  className="flex-1 px-3 py-2 text-base-ui font-medium text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg dark:focus:ring-lia-border-subtle focus:border-transparent transition-colors motion-reduce:transition-none"
                  placeholder={t('stageNamePlaceholder')}
                />
              ) : (
                <span className={`flex-1 ${textStyles.bodyLarge} font-medium px-3 py-2`}>
                  {getStageDisplayName(stage)}
                </span>
              )}
              <div className="flex items-center gap-2 flex-wrap">
                {getTypeBadge(stage.type)}
                <ActionBehaviorBadge behavior={stage.action_behavior} />
                {canEditName && (
                  <div className="flex items-center gap-2">
                    <Label htmlFor={`active-${stage.id}`} className={textStyles.description}>{t('active')}</Label>
                    <Switch
                      id={`active-${stage.id}`}
                      data-toggle="is_active"
                      data-testid={`pipeline-stage-active-toggle-${stage.name}`}
                      checked={stage.isActive}
                      onCheckedChange={(checked: boolean) => onUpdate(stage.id, { isActive: checked })}
                    />
                  </div>
                )}
              </div>
            </div>

            {canEditName && (
              <textarea
                data-field="notes"
                data-testid={`pipeline-stage-notes-${stage.name}`}
                value={stage.notes}
                onChange={(e) => onUpdate(stage.id, { notes: e.target.value })}
                placeholder={t('notesPlaceholder')}
                className="w-full px-3 py-2 text-xs text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg dark:focus:ring-lia-border-subtle focus:border-transparent transition-colors motion-reduce:transition-none resize-none"
                rows={2}
              />
            )}

            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-lia-text-secondary" />
                  <Label htmlFor={`sla-${stage.id}`} className={textStyles.description}>{t('sla')}</Label>
                  <div className="flex items-center gap-1">
                    <input
                      id={`sla-${stage.id}`}
                      type="number"
                      data-field="sla"
                      data-testid={`pipeline-stage-sla-${stage.name}`}
                      value={stage.sla}
                      onChange={(e) => onUpdate(stage.id, { sla: parseInt(e.target.value) || 0 })}
                      className="w-14 px-2 py-1 text-xs text-center text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg dark:focus:ring-lia-border-subtle focus:border-transparent transition-colors motion-reduce:transition-none"
                      min={0} max={30}
                    />
                    <span className={textStyles.caption}>{t('slaDays')}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Label className={textStyles.description}>{t('action')}</Label>
                  <select
                    data-field="action_behavior"
                    data-testid={`pipeline-stage-action-behavior-${stage.name}`}
                    value={stage.action_behavior || 'passive'}
                    onChange={(e) => onUpdate(stage.id, { action_behavior: e.target.value })}
                    className="px-2 py-1 text-xs text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg dark:focus:ring-lia-border-subtle focus:border-transparent transition-colors motion-reduce:transition-none"
                  >
                    <option value="passive">{t('actionPassive')}</option>
                    <option value="screening">{t('actionScreening')}</option>
                    <option value="scheduling">{t('actionScheduling')}</option>
                    <option value="evaluation">{t('actionEvaluation')}</option>
                    <option value="verification">{t('actionVerification')}</option>
                    <option value="offer">{t('actionOffer')}</option>
                    <option value="intake">{t('actionIntake')}</option>
                    <option value="conclusion_hired">{t('actionConclusionHired')}</option>
                    <option value="conclusion_rejected">{t('actionConclusionRejected')}</option>
                    <option value="conclusion_declined">{t('actionConclusionDeclined')}</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <Label className={textStyles.description}>{t('channel')}</Label>
                  <select
                    data-field="default_channel"
                    data-testid={`pipeline-stage-default-channel-${stage.name}`}
                    value={stage.default_channel || 'email'}
                    onChange={(e) => onUpdate(stage.id, { default_channel: e.target.value })}
                    className="px-2 py-1 text-xs text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg dark:focus:ring-lia-border-subtle focus:border-transparent transition-colors motion-reduce:transition-none"
                  >
                    <option value="email">{t('channelEmail')}</option>
                    <option value="whatsapp">{t('channelWhatsapp')}</option>
                    <option value="email_whatsapp">{t('channelEmailWhatsapp')}</option>
                  </select>
                </div>
              </div>

              {canRemove && (
                <Button
                  data-testid={`pipeline-stage-remove-${stage.name}`}
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemove(stage.id)}
                  className="text-lia-text-tertiary hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20 transition-colors motion-reduce:transition-none"
                  aria-label={t('removeStage', { name: getStageDisplayName(stage) })}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>

            <SubStatusPanel
              stage={stage}
              isEditMode={isEditMode}
              onToggleSubStatus={onToggleSubStatus}
            />

            <DataFieldsPanel
              stage={stage}
              isEditMode={isEditMode}
              onUpdate={onUpdate}
            />

            <SaturationControlPanel
              stage={stage}
              isEditMode={isEditMode}
            />
          </div>
        </div>
      </Card>
    </div>
  )
}
