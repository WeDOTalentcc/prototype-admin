"use client"

import React, { useState } from "react"
import { Briefcase, Database, GitBranch, List, Zap, Calendar, MousePointer } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, buttonStyles, textStyles, inputStyles } from "@/lib/design-tokens"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog"
import { toast } from "@/lib/toast"
import type { CustomAgent, DeploymentTargetType, TriggerMode } from "./types"

const TARGET_OPTIONS: { type: DeploymentTargetType; icon: React.ReactNode; descKey: string }[] = [
  { type: "job", icon: <Briefcase className="w-4 h-4" />, descKey: "targetDescJob" },
  { type: "talent_pool", icon: <Database className="w-4 h-4" />, descKey: "targetDescPool" },
  { type: "pipeline_stage", icon: <GitBranch className="w-4 h-4" />, descKey: "targetDescStage" },
  { type: "candidate_list", icon: <List className="w-4 h-4" />, descKey: "targetDescList" },
]

const TRIGGER_OPTIONS: { mode: TriggerMode; icon: React.ReactNode }[] = [
  { mode: "on_new_candidate", icon: <Zap className="w-3.5 h-3.5" /> },
  { mode: "on_stage_change", icon: <GitBranch className="w-3.5 h-3.5" /> },
  { mode: "manual", icon: <MousePointer className="w-3.5 h-3.5" /> },
  { mode: "scheduled", icon: <Calendar className="w-3.5 h-3.5" /> },
]

interface DeployDialogProps {
  agent: CustomAgent | null
  open: boolean
  onClose: () => void
  onDeployed: () => void
}

export function DeployDialog({ agent, open, onClose, onDeployed }: DeployDialogProps) {
  const t = useTranslations('agents.customAgents')
  const [targetType, setTargetType] = useState<DeploymentTargetType>("job")
  const [targetId, setTargetId] = useState("")
  const [targetName, setTargetName] = useState("")
  const [triggerMode, setTriggerMode] = useState<TriggerMode>("on_new_candidate")
  const [isDeploying, setIsDeploying] = useState(false)

  const handleDeploy = async () => {
    if (!agent || !targetId.trim()) return
    setIsDeploying(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/deployments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          target_type: targetType,
          target_id: targetId,
          target_name: targetName || undefined,
          trigger_mode: triggerMode,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: t('errors.errorBinding') }))
        throw new Error(err.detail || t('errors.errorBinding'))
      }
      toast.success(t('agentLinkedSuccess'))
      onDeployed()
      onClose()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('errors.errorBinding'))
    } finally {
      setIsDeploying(false)
    }
  }

  if (!agent) return null

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className={textStyles.title}>
            {t('deployTitle', { name: agent.name })}
          </DialogTitle>
          <p className={cn(textStyles.caption, "mt-1")}>
            {t('deployDesc')}
          </p>
        </DialogHeader>

        <div className="space-y-5 py-2">
          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-2 block">
              {t('whereLabel')}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {TARGET_OPTIONS.map((opt) => (
                <button
                  key={opt.type}
                  type="button"
                  onClick={() => setTargetType(opt.type)}
                  className={cn(
                    targetType === opt.type ? cardStyles.selected : cardStyles.interactive,
                    "p-3 text-left"
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-graphite">{opt.icon}</span>
                    <span className="text-xs font-semibold text-lia-text-primary">
                      {t('targets.' + opt.type)}
                    </span>
                  </div>
                  <p className="text-[10px] text-lia-text-disabled leading-tight">{t(opt.descKey)}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">
                {t('targetIdLabel', { target: t('targets.' + targetType) })}
              </label>
              <input
                type="text"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                placeholder={t('idPlaceholder')}
                className={cn(inputStyles.default, "text-xs")}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">
                {t('nameOptional')}
              </label>
              <input
                type="text"
                value={targetName}
                onChange={(e) => setTargetName(e.target.value)}
                placeholder={t('namePlaceholder')}
                className={cn(inputStyles.default, "text-xs")}
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-2 block">
              {t('whenLabel')}
            </label>
            <div className="flex flex-wrap gap-1.5">
              {TRIGGER_OPTIONS.map((opt) => (
                <button
                  key={opt.mode}
                  type="button"
                  onClick={() => setTriggerMode(opt.mode)}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                    triggerMode === opt.mode
                      ? "bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary"
                      : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active"
                  )}
                >
                  {opt.icon}
                  {t('triggers.' + opt.mode)}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <button type="button" onClick={onClose} className={cn(buttonStyles.ghost, "text-xs px-3 py-1.5")}>
            {t('cancelBtn')}
          </button>
          <button
            type="button"
            onClick={handleDeploy}
            disabled={!targetId.trim() || isDeploying}
            className={cn(buttonStyles.primary, "text-xs px-4 py-1.5")}
          >
            {isDeploying ? t('linkingBtn') : t('linkAndActivate')}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
