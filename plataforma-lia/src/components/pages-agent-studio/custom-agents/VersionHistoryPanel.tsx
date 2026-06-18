"use client"

import React, { useState } from "react"
import { History, RotateCcw, Loader2, ChevronRight } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles, buttonStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { ConfirmAlertDialog } from "@/components/agent-studio/confirm-alert-dialog"
import { useAgentVersions } from "@/hooks/agents"

interface VersionHistoryPanelProps {
  agentId: string
  currentVersion: number
  onReverted?: () => void
}

export function VersionHistoryPanel({ agentId, currentVersion, onReverted }: VersionHistoryPanelProps) {
  const t = useTranslations('agents.customAgents')
  const tToast = useTranslations('agents.toast')
  const { versions, isLoading, mutate } = useAgentVersions(agentId)
  const [revertingVersion, setRevertingVersion] = useState<number | null>(null)

  // Sprint B QW#4 audit 2026-05-22: state-driven confirm via shadcn AlertDialog
  const [revertTargetVersion, setRevertTargetVersion] = useState<number | null>(null)
  useLiaModalTracking('version-history-revert-confirm', revertTargetVersion !== null)

  const handleRevert = (version: number) => {
    setRevertTargetVersion(version)
  }

  const confirmRevert = async () => {
    const version = revertTargetVersion
    if (version === null) return
    setRevertTargetVersion(null)
    setRevertingVersion(version)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agentId}/revert/${version}`, {
        method: "POST",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error" }))
        throw new Error(err.detail || tToast('revertError'))
      }
      toast.success(tToast('revertedTo', { version }))
      mutate()
      onReverted?.()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : tToast('revertError'))
    } finally {
      setRevertingVersion(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-xs text-lia-text-muted">
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> {t('loadingHistory')}
      </div>
    )
  }

  if (versions.length === 0) {
    return (
      <div className={cn(cardStyles.flat, "p-4 text-center")}>
        <History className="w-6 h-6 text-lia-text-muted mx-auto mb-1.5" />
        <p className="text-xs text-lia-text-secondary">{t('noVersions')}</p>
        <p className="text-[10px] text-lia-text-muted mt-1">{t('snapshotsAutoCreated')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 mb-2">
        <History className="w-3.5 h-3.5 text-lia-text-muted" />
        <h4 className={cn(textStyles.subtitle, "text-xs font-semibold")}>
          {t('versionHistory')}
        </h4>
        <span className={cn(badgeStyles.default, "text-[10px] ml-auto")}>
          {t('currentVersion', { version: currentVersion })}
        </span>
      </div>

      <div className="space-y-1.5 max-h-64 overflow-auto">
        {versions.map((v) => {
          const isReverting = revertingVersion === v.version
          const date = v.created_at ? new Date(v.created_at).toLocaleString(undefined, {
            day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
          }) : ""

          return (
            <div key={v.id} className={cn(cardStyles.compact, "flex items-center justify-between")}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={cn(badgeStyles.default, "text-[10px]")}>v{v.version}</span>
                  <span className="text-[10px] text-lia-text-muted">{date}</span>
                </div>
                {v.changed_fields.length > 0 && (
                  <p className="text-[10px] text-lia-text-secondary mt-0.5 truncate">
                    {t('changed')}: {v.changed_fields.slice(0, 3).join(", ")}
                    {v.changed_fields.length > 3 && ` +${v.changed_fields.length - 3}`}
                  </p>
                )}
                {v.change_reason && (
                  <p className="text-[10px] text-lia-text-muted italic mt-0.5 truncate">{v.change_reason}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => handleRevert(v.version)}
                disabled={isReverting || v.version >= currentVersion}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                title={v.version >= currentVersion ? t('alreadyCurrent') : t('revertToVersion')}
              >
                {isReverting ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RotateCcw className="w-3 h-3" />
                )}
                {t('revert')}
              </button>
            </div>
          )
        })}
      </div>
                {/* Sprint B QW#4 audit 2026-05-22: ConfirmAlertDialog canonical */}
      <ConfirmAlertDialog
        open={revertTargetVersion !== null}
        onOpenChange={(open) => !open && setRevertTargetVersion(null)}
        title={t('confirmRevertTitle') || 'Reverter versão?'}
        description={revertTargetVersion !== null ? t('confirmRevert', { version: revertTargetVersion }) : ''}
        onConfirm={confirmRevert}
        confirmLabel={t('revert') || 'Reverter'}
      />

      </div>
  )
}
