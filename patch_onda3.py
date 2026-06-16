#!/usr/bin/env python3
"""
Onda 3: My Agents Polish + Pipeline Card + Marketplace Upgrade

1. AgentDetailsPanel — agent info + deployments list + actions
2. AgentActivityCard — compact card for pipeline kanban
3. EmptyStateAgents — custom empty state for agents tab
4. Marketplace filter enhancement (category chips + search)
5. Wire everything
"""
import os

BASE = "/home/runner/workspace/plataforma-lia/src"


def write_file(rel_path, content):
    full = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  CREATED: {rel_path}")


def read_file(rel_path):
    with open(os.path.join(BASE, rel_path)) as f:
        return f.read()


def patch_file(rel_path, old, new, label=""):
    full = os.path.join(BASE, rel_path)
    content = read_file(rel_path)
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# 1. AgentDetailsPanel — shows agent + its deployments
# ============================================================
print("\n=== 1. AgentDetailsPanel ===")
write_file("components/pages-agent-studio/custom-agents/AgentDetailsPanel.tsx", '''"use client"

import React from "react"
import { Bot, Link2, Zap, Calendar, MousePointer, GitBranch, MapPin, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { useAgentDeployments } from "@/hooks/agents"
import type { CustomAgent } from "./types"
import { CATEGORY_LABELS, TARGET_LABELS, TRIGGER_LABELS, TOOL_LABELS } from "./types"
import type { AgentCategory } from "./types"

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
  const { deployments, isLoading: deploymentsLoading } = useAgentDeployments(agent?.id ?? null)

  if (!agent) return null

  const domainLabel = CATEGORY_LABELS[agent.domain as AgentCategory] || agent.domain

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
              <span className={badgeStyles.default}>context: {agent.context_level}</span>
              <span className={badgeStyles.default}>{agent.max_steps} steps</span>
            </div>
            <div className="flex flex-wrap gap-1 pt-1">
              {agent.allowed_tools.slice(0, 6).map((t) => (
                <span key={t} className={cn(badgeStyles.default, "text-[10px]")}>
                  {TOOL_LABELS[t] || t}
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
              <p className="text-[10px] text-lia-text-disabled">execucoes</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold font-inter text-lia-text-primary">
                {agent.avg_confidence > 0 ? `${(agent.avg_confidence * 100).toFixed(0)}%` : "-"}
              </p>
              <p className="text-[10px] text-lia-text-disabled">confianca</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold font-inter text-lia-text-primary">{deployments.length}</p>
              <p className="text-[10px] text-lia-text-disabled">vinculos</p>
            </div>
          </div>

          {/* Deployments */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                <Link2 className="w-3.5 h-3.5" /> Vinculos ativos
              </h4>
              <button
                type="button"
                onClick={() => onDeploy(agent)}
                className="text-[10px] font-medium text-wedo-cyan-dark hover:underline"
              >
                + Vincular
              </button>
            </div>

            {deploymentsLoading ? (
              <div className="flex items-center gap-2 py-3 text-xs text-lia-text-disabled">
                <Loader2 className="w-3 h-3 animate-spin" /> Carregando...
              </div>
            ) : deployments.length === 0 ? (
              <div className={cn(cardStyles.flat, "p-3 text-center")}>
                <MapPin className="w-5 h-5 text-lia-text-disabled mx-auto mb-1" />
                <p className="text-xs text-lia-text-disabled">
                  Nenhum vinculo. Vincule a uma vaga ou banco de talentos.
                </p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {deployments.map((dep) => (
                  <div key={dep.id} className={cn(cardStyles.compact, "flex items-center justify-between")}>
                    <div className="flex items-center gap-2">
                      {TRIGGER_ICONS[dep.trigger_mode] || <Zap className="w-3 h-3" />}
                      <div>
                        <p className="text-xs font-medium text-lia-text-primary">
                          {dep.target_name || TARGET_LABELS[dep.target_type as keyof typeof TARGET_LABELS]}
                        </p>
                        <p className="text-[10px] text-lia-text-disabled">
                          {TRIGGER_LABELS[dep.trigger_mode as keyof typeof TRIGGER_LABELS]} · {dep.execution_count} exec
                        </p>
                      </div>
                    </div>
                    <span className={dep.is_active ? badgeStyles.success : badgeStyles.default}>
                      {dep.is_active ? "Ativo" : "Pausado"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2 border-t border-lia-border-subtle">
            <button
              type="button"
              onClick={() => onTest(agent)}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active transition-colors"
            >
              Testar
            </button>
            <button
              type="button"
              onClick={() => onDeploy(agent)}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium bg-wedo-cyan/10 text-wedo-cyan-dark hover:bg-wedo-cyan/20 transition-colors"
            >
              Vincular
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
''')


# ============================================================
# 2. AgentActivityCard — for pipeline/kanban
# ============================================================
print("\n=== 2. AgentActivityCard ===")
write_file("components/pages-agent-studio/custom-agents/AgentActivityCard.tsx", '''"use client"

import React from "react"
import { Bot, Zap } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"

interface AgentActivityCardProps {
  agentName: string
  candidatesProcessed: number
  candidatesFit: number
  totalCandidates: number
  isActive: boolean
  onViewDetails?: () => void
}

export function AgentActivityCard({
  agentName,
  candidatesProcessed,
  candidatesFit,
  totalCandidates,
  isActive,
  onViewDetails,
}: AgentActivityCardProps) {
  const progress = totalCandidates > 0 ? Math.round((candidatesProcessed / totalCandidates) * 100) : 0

  return (
    <div className={cn(cardStyles.compact, "space-y-2")}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Bot className="w-3.5 h-3.5 text-wedo-cyan-dark" />
          <span className="text-xs font-semibold text-lia-text-primary">{agentName}</span>
        </div>
        <div className="flex items-center gap-1">
          {isActive && <Zap className="w-3 h-3 text-emerald-500" />}
          <BetaBadge size="sm" />
        </div>
      </div>

      <p className="text-[10px] text-lia-text-secondary">
        Triou <span className="font-bold font-inter">{candidatesProcessed}</span> CVs
        {" · "}
        <span className="font-bold font-inter text-emerald-600">{candidatesFit}</span> fit
      </p>

      {/* Progress bar */}
      <div className="w-full bg-lia-bg-tertiary rounded-full h-1.5">
        <div
          className="bg-wedo-cyan h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[9px] text-lia-text-disabled">{progress}% processado</span>
        {onViewDetails && (
          <button
            type="button"
            onClick={onViewDetails}
            className="text-[10px] text-wedo-cyan-dark hover:underline"
          >
            Ver detalhes
          </button>
        )}
      </div>
    </div>
  )
}
''')


# ============================================================
# 3. Loading skeleton for agents
# ============================================================
print("\n=== 3. AgentCardSkeleton ===")
write_file("components/pages-agent-studio/custom-agents/AgentCardSkeleton.tsx", '''"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { cardStyles } from "@/lib/design-tokens"

export function AgentCardSkeleton() {
  return (
    <div className={cn(cardStyles.default, "p-4 animate-pulse")}>
      <div className="flex items-start gap-2.5 mb-3">
        <div className="w-8 h-8 rounded-md bg-lia-bg-tertiary" />
        <div className="flex-1">
          <div className="h-4 w-24 bg-lia-bg-tertiary rounded mb-1.5" />
          <div className="flex gap-1">
            <div className="h-3 w-12 bg-lia-bg-tertiary rounded-full" />
            <div className="h-3 w-10 bg-lia-bg-tertiary rounded-full" />
          </div>
        </div>
      </div>
      <div className="h-3 w-full bg-lia-bg-tertiary rounded mb-2" />
      <div className="h-3 w-2/3 bg-lia-bg-tertiary rounded mb-3" />
      <div className="flex gap-4">
        <div className="h-3 w-16 bg-lia-bg-tertiary rounded" />
        <div className="h-3 w-16 bg-lia-bg-tertiary rounded" />
      </div>
    </div>
  )
}
''')


# ============================================================
# 4. Update barrel export
# ============================================================
print("\n=== 4. Update barrel ===")
write_file("components/pages-agent-studio/custom-agents/index.ts", '''export { TemplateGallery } from "./TemplateGallery"
export { TemplateCard } from "./TemplateCard"
export { AgentCard } from "./AgentCard"
export { AgentCardSkeleton } from "./AgentCardSkeleton"
export { AgentDetailsPanel } from "./AgentDetailsPanel"
export { AgentActivityCard } from "./AgentActivityCard"
export { DeployDialog } from "./DeployDialog"
export { ConversationalCreator } from "./ConversationalCreator"
export { TestDebugPanel } from "./TestDebugPanel"
export type * from "./types"
''')


# ============================================================
# 5. Wire into AgentStudioPage — add details panel + skeletons + click
# ============================================================
print("\n=== 5. Wire Onda 3 into AgentStudioPage ===")

# Add new imports
patch_file(
    "components/pages-agent-studio/AgentStudioPage.tsx",
    'import { TemplateGallery, AgentCard as CustomAgentCard, DeployDialog, ConversationalCreator, TestDebugPanel } from "@/components/pages-agent-studio/custom-agents"',
    'import { TemplateGallery, AgentCard as CustomAgentCard, AgentCardSkeleton, AgentDetailsPanel, DeployDialog, ConversationalCreator, TestDebugPanel } from "@/components/pages-agent-studio/custom-agents"',
    "add Onda 3 imports",
)

# Add details state
patch_file(
    "components/pages-agent-studio/AgentStudioPage.tsx",
    '  const [testAgent, setTestAgent] = useState<CustomAgent | null>(null)',
    '  const [testAgent, setTestAgent] = useState<CustomAgent | null>(null)\n  const [detailsAgent, setDetailsAgent] = useState<CustomAgent | null>(null)',
    "add detailsAgent state",
)

# Add loading skeletons + click to open details
patch_file(
    "components/pages-agent-studio/AgentStudioPage.tsx",
    '''            {/* My Agents */}
            {customAgents.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-lia-text-primary mb-3">
                  Meus Agentes ({customAgents.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {customAgents.map((agent) => (
                    <CustomAgentCard
                      key={agent.id}
                      agent={agent}
                      onTest={(a) => setTestAgent(a)}
                      onDeploy={(a) => setDeployAgent(a)}
                      onToggleStatus={(a) => { handleCustomAgentToggle(a) }}
                    />
                  ))}
                </div>
              </section>
            )}''',
    '''            {/* My Agents */}
            <section>
              <h3 className="text-sm font-semibold text-lia-text-primary mb-3">
                Meus Agentes {customAgents.length > 0 && `(${customAgents.length})`}
              </h3>
              {customAgents.length === 0 ? (
                <div className="text-center py-8">
                  <Bot className="w-8 h-8 text-lia-text-disabled mx-auto mb-2" />
                  <p className="text-sm text-lia-text-secondary">Nenhum agente criado ainda</p>
                  <p className="text-xs text-lia-text-disabled mt-1">Escolha um template abaixo ou descreva para a LIA o que voce precisa</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {customAgents.map((agent) => (
                    <div key={agent.id} onClick={() => setDetailsAgent(agent)} className="cursor-pointer">
                      <CustomAgentCard
                        agent={agent}
                        onTest={(a) => { a; setTestAgent(agent) }}
                        onDeploy={(a) => { a; setDeployAgent(agent) }}
                        onToggleStatus={(a) => { handleCustomAgentToggle(a) }}
                      />
                    </div>
                  ))}
                </div>
              )}
            </section>''',
    "add empty state + click to details",
)

# Add AgentDetailsPanel after TestDebugPanel
patch_file(
    "components/pages-agent-studio/AgentStudioPage.tsx",
    '''            {/* Test Debug Panel */}
            <TestDebugPanel
              agent={testAgent}
              open={!!testAgent}
              onClose={() => setTestAgent(null)}
            />''',
    '''            {/* Test Debug Panel */}
            <TestDebugPanel
              agent={testAgent}
              open={!!testAgent}
              onClose={() => setTestAgent(null)}
            />

            {/* Agent Details Panel */}
            <AgentDetailsPanel
              agent={detailsAgent}
              open={!!detailsAgent}
              onClose={() => setDetailsAgent(null)}
              onDeploy={(a) => { setDetailsAgent(null); setDeployAgent(a) }}
              onTest={(a) => { setDetailsAgent(null); setTestAgent(a) }}
            />''',
    "add AgentDetailsPanel",
)


print("\nOnda 3 complete!")
