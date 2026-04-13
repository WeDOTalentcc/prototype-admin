"use client"

import React, { useState } from "react"
import { Briefcase, Database, GitBranch, List, Zap, Calendar, MousePointer } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, buttonStyles, textStyles, inputStyles } from "@/lib/design-tokens"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog"
import { toast } from "@/lib/toast"
import type { CustomAgent, DeploymentTargetType, TriggerMode } from "./types"
import { TARGET_LABELS, TRIGGER_LABELS } from "./types"

const TARGET_OPTIONS: { type: DeploymentTargetType; icon: React.ReactNode; desc: string }[] = [
  { type: "job", icon: <Briefcase className="w-4 h-4" />, desc: "Atuar nos candidatos de uma vaga" },
  { type: "talent_pool", icon: <Database className="w-4 h-4" />, desc: "Atuar num banco de talentos" },
  { type: "pipeline_stage", icon: <GitBranch className="w-4 h-4" />, desc: "Atuar quando candidato chegar numa etapa" },
  { type: "candidate_list", icon: <List className="w-4 h-4" />, desc: "Atuar numa lista especifica de candidatos" },
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
        const err = await res.json().catch(() => ({ detail: "Erro ao vincular" }))
        throw new Error(err.detail || "Erro ao vincular")
      }
      toast.success(`Agente vinculado com sucesso!`)
      onDeployed()
      onClose()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao vincular agente")
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
            Vincular &ldquo;{agent.name}&rdquo;
          </DialogTitle>
          <p className={cn(textStyles.caption, "mt-1")}>
            Escolha onde e quando o agente vai atuar
          </p>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* Target Type */}
          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-2 block">
              Onde vai atuar?
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
                    <span className="text-wedo-cyan-dark">{opt.icon}</span>
                    <span className="text-xs font-semibold text-lia-text-primary">
                      {TARGET_LABELS[opt.type]}
                    </span>
                  </div>
                  <p className="text-[10px] text-lia-text-disabled leading-tight">{opt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Target ID + Name */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">
                ID do {TARGET_LABELS[targetType]}
              </label>
              <input
                type="text"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                placeholder="UUID ou identificador"
                className={cn(inputStyles.default, "text-xs")}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">
                Nome (opcional)
              </label>
              <input
                type="text"
                value={targetName}
                onChange={(e) => setTargetName(e.target.value)}
                placeholder="Ex: Vaga Dev Python Sr"
                className={cn(inputStyles.default, "text-xs")}
              />
            </div>
          </div>

          {/* Trigger Mode */}
          <div>
            <label className="text-xs font-semibold text-lia-text-primary mb-2 block">
              Quando ativar?
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
                  {TRIGGER_LABELS[opt.mode]}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <button type="button" onClick={onClose} className={cn(buttonStyles.ghost, "text-xs px-3 py-1.5")}>
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleDeploy}
            disabled={!targetId.trim() || isDeploying}
            className={cn(buttonStyles.primary, "text-xs px-4 py-1.5")}
          >
            {isDeploying ? "Vinculando..." : "Vincular e Ativar"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
