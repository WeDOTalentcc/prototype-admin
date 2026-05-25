"use client"

import React, { useState } from "react"
import { Bot, Link2, Zap, Calendar, MousePointer, GitBranch, MapPin, Loader2, Copy } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { useAgentDeployments } from "@/hooks/agents"
import { VersionHistoryPanel } from "./VersionHistoryPanel"
import type { CustomAgent } from "./types"
import { safeCategoryKey } from "./types"

const TRIGGER_ICONS: Record<string, React.ReactNode> = {
  manual: <MousePointer className="w-3 h-3" />,
  on_new_candidate: <Zap className="w-3 h-3" />,
  on_stage_change: <GitBranch className="w-3 h-3" />,
  scheduled: <Calendar className="w-3 h-3" />,
}

interface AgentDetailsPanelProps {
  agent: CustomAgent | null
  open: boolean
  onClose: () => void
  onDeploy: (agent: CustomAgent) => void
  onTest: (agent: CustomAgent) => void
}

export function AgentDetailsPanel({ agent, open, onClose, onDeploy, onTest }: AgentDetailsPanelProps) {
  const t = useTranslations('agents.customAgents')
  const tStatus = useTranslations('agents.status')
  const { deployments, isLoading: deploymentsLoading } = useAgentDeployments(agent?.id ?? null)
  const [isCloning, setIsCloning] = useState(false)

  const handleClone = async () => {
    if (!agent) return
    setIsCloning(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/clone`, {
        method: "POST",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok) throw new Error(t('errors.errorCloning'))
      onClose()
    } catch {
      // toast handled by caller
    } finally {
      setIsCloning(false)
    }
  }

  if (!agent) return null

  const domainLabel = t('categories.' + safeCategoryKey(agent.domain)) || agent.domain || 'general'

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className={cn(textStyles.title, "flex items-center gap-2")}>
            <Bot className="w-5 h-5 text-wedo-cyan-dark" />
            {agent.name}
            <BetaBadge size="sm" />
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Info */}
          <div className="space-y-2">
            {agent.description && (
              <p className={cn(textStyles.caption, "text-xs")}>{agent.description}</p>
            )}
            <div className="flex flex-wrap gap-1.5">
              <span className={badgeStyles.cyan}>{domainLabel}</span>
              <span className={badgeStyles.default}>{t('contextLabel')}: {agent.context_level}</span>
              <span className={badgeStyles.default}>{agent.max_steps} {t('stepsLabel')}</span>
            </div>
            <div className="flex flex-wrap gap-1 pt-1">
              {agent.allowed_tools.slice(0, 6).map((tool) => (
                <span key={tool} className={cn(badgeStyles.default, "text-[10px]")}>
                  {t('tools.' + tool) || tool}
                </span>
              ))}
              {agent.allowed_tools.length > 6 && (
                <span className={cn(badgeStyles.default, "text-[10px]")}>
                  +{agent.allowed_tools.length - 6}
                </span>
              )}
            </div>
          </div>

          {/* Metrics */}
          <div className={cn(cardStyles.flat, "p-3 flex items-center gap-6")}>
            <div className="text-center">
              <p className="text-lg font-bold font-inter text-lia-text-primary">{agent.total_executions}</p>
              <p className="text-xs text-lia-text-secondary">{t('execLabel')}</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold font-inter text-lia-text-primary">
                {agent.avg_confidence > 0 ? `${(agent.avg_confidence * 100).toFixed(0)}%` : "-"}
              </p>
              <p className="text-xs text-lia-text-secondary">{t('confidence')}</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold font-inter text-lia-text-primary">{deployments.length}</p>
              <p className="text-xs text-lia-text-secondary">{t('links')}</p>
            </div>
          </div>

          {/* Deployments */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                <Link2 className="w-3.5 h-3.5" /> {t('activeDeployments')}
              </h4>
              <button
                type="button"
                onClick={() => onDeploy(agent)}
                className="text-[10px] font-medium text-wedo-cyan-dark hover:underline"
              >
                {t('addLink')}
              </button>
            </div>

            {deploymentsLoading ? (
              <div className="flex items-center gap-2 py-3 text-xs text-lia-text-disabled">
                <Loader2 className="w-3 h-3 animate-spin" /> {t('loadingLinks')}
              </div>
            ) : deployments.length === 0 ? (
              <div className={cn(cardStyles.flat, "p-3 text-center")}>
                <MapPin className="w-5 h-5 text-lia-text-disabled mx-auto mb-1" />
                <p className="text-xs text-lia-text-disabled">
                  {t('noLinks')}
                </p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {deployments.map((dep: { id: string; trigger_mode: string; target_name?: string | null; target_type?: string | null; execution_count?: number; is_active?: boolean }) => (
                  <div key={dep.id} className={cn(cardStyles.compact, "flex items-center justify-between")}>
                    <div className="flex items-center gap-2">
                      {TRIGGER_ICONS[dep.trigger_mode] || <Zap className="w-3 h-3" />}
                      <div>
                        <p className="text-xs font-medium text-lia-text-primary">
                          {dep.target_name || t('targets.' + dep.target_type) || dep.target_type}
                        </p>
                        <p className="text-xs text-lia-text-secondary">
                          {t('triggers.' + dep.trigger_mode) || dep.trigger_mode} · {dep.execution_count} {t('exec')}
                        </p>
                      </div>
                    </div>
                    <span className={dep.is_active ? badgeStyles.success : badgeStyles.default}>
                      {dep.is_active ? tStatus('active') : tStatus('paused')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Version History */}
          <div className="pt-2 border-t border-lia-border-subtle">
            <VersionHistoryPanel
              agentId={agent.id}
              currentVersion={(agent as unknown as { version?: number }).version || 1}
              onReverted={() => {
              }}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2 border-t border-lia-border-subtle">
            <button
              type="button"
              onClick={() => onTest(agent)}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active transition-colors"
            >
              {t('testBtn')}
            </button>
            <button
              type="button"
              onClick={() => onDeploy(agent)}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium bg-wedo-cyan/10 text-wedo-cyan-dark hover:bg-wedo-cyan/20 transition-colors"
            >
              {t('linkBtn')}
            </button>
            <button
              type="button"
              onClick={handleClone}
              disabled={isCloning}
              className="inline-flex items-center justify-center gap-1 px-3 py-2 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
            >
              <Copy className="w-3.5 h-3.5" />
              {isCloning ? t('cloning') : t('clone')}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
