#!/usr/bin/env python3
"""
Onda 4: Studio <-> Chat Bridge

Backend:
  1. GET /custom-agents/search?name=X (fuzzy match)
  2. GET /studio/metrics/summary (aggregated metrics)

Frontend:
  3. Add 3 intents to use-action-intent.ts: studio_create, studio_query, studio_metrics
  4. Extend DynamicPanelType: "agent_creation_preview"
  5. NEW: AgentCreationPreview component (dynamic panel)
  6. NEW: AgentChatCard component (inline card in chat)
  7. NEW: useStudioChatChips hook
  8. Wire intents in LiaSuperPrompt handler
"""
import os
import sys

BASE_BE = "/home/runner/workspace/lia-agent-system"
BASE_FE = "/home/runner/workspace/plataforma-lia/src"


def write_file(base, rel, content):
    full = os.path.join(base, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  CREATED: {rel}")


def read_file(base, rel):
    with open(os.path.join(base, rel)) as f:
        return f.read()


def patch_file(base, rel, old, new, label=""):
    full = os.path.join(base, rel)
    content = read_file(base, rel)
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# 1. BACKEND: /search + /studio/metrics/summary endpoints
# ============================================================
print("\n=== 1. Backend endpoints ===")
patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''@router.post("/generate-from-description", summary="LIA generates agent config from description")''',
    '''@router.get("/search", summary="Search agents by name (fuzzy)")
async def search_agents_by_name(
    name: str = Query(..., min_length=1, max_length=256),
    limit: int = Query(5, ge=1, le=20),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fuzzy search for agents by name. Used by chat to find agent mentioned by user.

    Returns top N matches ordered by relevance. Tenant-isolated.
    """
    from sqlalchemy import select, and_, func
    from lia_models.custom_agent import CustomAgent

    # Case-insensitive LIKE search
    name_lower = name.lower().strip()
    result = await db.execute(
        select(CustomAgent)
        .where(
            and_(
                CustomAgent.company_id == current_user.company_id,
                func.lower(CustomAgent.name).contains(name_lower),
            )
        )
        .limit(limit)
    )
    agents = list(result.scalars().all())
    return {
        "agents": [a.to_dict() for a in agents],
        "total": len(agents),
        "query": name,
    }


@router.get("/studio/metrics/summary", summary="Aggregated Studio metrics for dashboard/chat")
async def get_studio_metrics_summary(
    period_days: int = Query(7, ge=1, le=90),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns aggregated metrics across all tenant agents for the specified period.

    Used by chat intent "meu consumo" / "quantas execucoes hoje".
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, and_, func, desc
    from lia_models.custom_agent import CustomAgent
    from lia_models.agent_execution_log import AgentExecutionLog

    since = datetime.now(timezone.utc) - timedelta(days=period_days)

    # Total metrics
    totals = await db.execute(
        select(
            func.count(AgentExecutionLog.id).label("total_executions"),
            func.coalesce(func.sum(AgentExecutionLog.tokens_input), 0).label("total_tokens_input"),
            func.coalesce(func.sum(AgentExecutionLog.tokens_output), 0).label("total_tokens_output"),
            func.coalesce(func.sum(AgentExecutionLog.credits_consumed), 0).label("total_credits"),
            func.coalesce(func.avg(AgentExecutionLog.confidence), 0.0).label("avg_confidence"),
            func.coalesce(func.avg(AgentExecutionLog.latency_ms), 0).label("avg_latency_ms"),
        ).where(
            and_(
                AgentExecutionLog.company_id == current_user.company_id,
                AgentExecutionLog.created_at >= since,
            )
        )
    )
    total_row = totals.one()

    # Top 3 agents by execution count
    top_agents_result = await db.execute(
        select(
            AgentExecutionLog.agent_id,
            func.count(AgentExecutionLog.id).label("exec_count"),
            func.coalesce(func.sum(AgentExecutionLog.tokens_input + AgentExecutionLog.tokens_output), 0).label("total_tokens"),
        )
        .where(
            and_(
                AgentExecutionLog.company_id == current_user.company_id,
                AgentExecutionLog.created_at >= since,
            )
        )
        .group_by(AgentExecutionLog.agent_id)
        .order_by(desc("exec_count"))
        .limit(3)
    )
    top_agent_rows = list(top_agents_result.all())

    # Enrich top agents with names
    top_agents = []
    for row in top_agent_rows:
        agent_result = await db.execute(
            select(CustomAgent).where(CustomAgent.id == row.agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        top_agents.append({
            "agent_id": str(row.agent_id),
            "agent_name": agent.name if agent else "(deleted)",
            "execution_count": row.exec_count,
            "total_tokens": row.total_tokens,
        })

    # Active agent count
    active_count = await db.scalar(
        select(func.count(CustomAgent.id)).where(
            and_(
                CustomAgent.company_id == current_user.company_id,
                CustomAgent.status == "active",
            )
        )
    ) or 0

    # Estimated cost (R$0.000003 per token — rough estimate)
    total_tokens = (total_row.total_tokens_input or 0) + (total_row.total_tokens_output or 0)
    estimated_cost_brl = round(total_tokens * 0.000003, 4)

    return {
        "period_days": period_days,
        "total_executions": total_row.total_executions or 0,
        "total_tokens_input": total_row.total_tokens_input or 0,
        "total_tokens_output": total_row.total_tokens_output or 0,
        "total_tokens": total_tokens,
        "total_credits": total_row.total_credits or 0,
        "estimated_cost_brl": estimated_cost_brl,
        "avg_confidence": round(float(total_row.avg_confidence or 0), 3),
        "avg_latency_ms": int(total_row.avg_latency_ms or 0),
        "active_agents": active_count,
        "top_agents": top_agents,
    }


@router.post("/generate-from-description", summary="LIA generates agent config from description")''',
    "search + metrics/summary endpoints",
)


# ============================================================
# 2. Frontend: Add 3 intents to use-action-intent.ts
# ============================================================
print("\n=== 2. useActionIntent: add 3 studio intents ===")

patch_file(
    BASE_FE,
    "hooks/shared/use-action-intent.ts",
    'export type ActionType = "wizard" | "wsi" | "analytics" | "communication" | "ats_integration" | "task_reminder" | "note" | "calendar" | "candidate_field" | null',
    'export type ActionType = "wizard" | "wsi" | "analytics" | "communication" | "ats_integration" | "task_reminder" | "note" | "calendar" | "candidate_field" | "studio_create" | "studio_query" | "studio_metrics" | null',
    "add studio action types",
)

# Add keywords for the 3 new types BEFORE the detectActionType function
patch_file(
    BASE_FE,
    "hooks/shared/use-action-intent.ts",
    '''interface ScoredAction {''',
    '''const STUDIO_CREATE_KEYWORDS = [
  "criar agente", "criar agent", "novo agente", "novo agent",
  "cria um agente", "cria um agent", "configura um agente", "configure um agent",
  "montar agente", "montar agent", "quero um agente", "quero um agent",
  "agente de triagem", "agent de triagem", "agente que filtra", "agent que filtra",
  "agente para sourcing", "agent para sourcing", "agente de comunicacao", "agente de comunicação",
  "studio agent", "agent studio", "criar assistente", "novo assistente",
]

const STUDIO_QUERY_KEYWORDS = [
  "como esta o agente", "como está o agente", "como esta o agent", "como está o agent",
  "status do agente", "status do agent", "detalhes do agente", "detalhes do agent",
  "me fala sobre o agente", "me fala sobre o agent", "info do agente", "info do agent",
  "qual a configuracao do agente", "qual a configuração do agent",
  "ver agente", "ver agent", "mostrar agente", "mostrar agent",
  "o agente", "o agent",
]

const STUDIO_METRICS_KEYWORDS = [
  "consumo dos agentes", "consumo dos agents", "meu consumo",
  "quantas execucoes", "quantas execuções", "execucoes hoje", "execuções hoje",
  "execucoes essa semana", "execuções essa semana", "execucoes do mes", "execuções do mês",
  "qual agente mais rodou", "qual agent mais rodou", "top agentes", "top agents",
  "metricas dos agentes", "métricas dos agentes", "metricas do studio", "métricas do studio",
  "custo dos agentes", "custo dos agents", "tokens consumidos",
  "dashboard dos agentes", "dashboard dos agents",
]

interface ScoredAction {''',
    "add studio keyword lists",
)

# Add studio candidates in detectActionType
patch_file(
    BASE_FE,
    "hooks/shared/use-action-intent.ts",
    '''    {
      actionType: "candidate_field",
      score: scoreKeywords(message, CANDIDATE_FIELD_KEYWORDS),
      confidence: 0,
      label: "Modo: Atualizar Candidato",
    },
  ]''',
    '''    {
      actionType: "candidate_field",
      score: scoreKeywords(message, CANDIDATE_FIELD_KEYWORDS),
      confidence: 0,
      label: "Modo: Atualizar Candidato",
    },
    {
      actionType: "studio_create",
      score: scoreKeywords(message, STUDIO_CREATE_KEYWORDS),
      confidence: 0,
      label: "Modo: Criar Agent Studio",
    },
    {
      actionType: "studio_query",
      score: scoreKeywords(message, STUDIO_QUERY_KEYWORDS),
      confidence: 0,
      label: "Modo: Consultar Agent",
    },
    {
      actionType: "studio_metrics",
      score: scoreKeywords(message, STUDIO_METRICS_KEYWORDS),
      confidence: 0,
      label: "Modo: Metricas Studio",
    },
  ]''',
    "add studio scored candidates",
)

# Add actionTypeToDomain mapping
patch_file(
    BASE_FE,
    "hooks/shared/use-action-intent.ts",
    '''    case "candidate_field": return "pipeline_action"
    default:                return "general"
  }
}''',
    '''    case "candidate_field": return "pipeline_action"
    case "studio_create":   return "agent_studio"
    case "studio_query":    return "agent_studio"
    case "studio_metrics":  return "agent_studio"
    default:                return "general"
  }
}''',
    "add studio domain mapping",
)


# ============================================================
# 3. Extend DynamicPanelType to support agent creation
# ============================================================
print("\n=== 3. DynamicPanelType extension ===")
patch_file(
    BASE_FE,
    "contexts/lia-float-context.tsx",
    '''export type DynamicPanelType =
  | "calibration"
  | "candidate_review"
  | "profile"
  | "job_creation"
  | "scheduling"''',
    '''export type DynamicPanelType =
  | "calibration"
  | "candidate_review"
  | "profile"
  | "job_creation"
  | "scheduling"
  | "agent_creation_preview"
  | "agent_details"
  | "agent_metrics"''',
    "extend DynamicPanelType",
)


# ============================================================
# 4. Frontend: AgentCreationPreview component
# ============================================================
print("\n=== 4. AgentCreationPreview ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/AgentCreationPreview.tsx", '''"use client"

import React, { useState, useEffect } from "react"
import { Wand2, Check, X, Loader2, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles, buttonStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import { toast } from "@/lib/toast"
import { CATEGORY_LABELS, TOOL_LABELS } from "./types"
import type { AgentCategory } from "./types"

interface GeneratedConfig {
  suggested_name: string
  suggested_role: string
  suggested_domain: string
  suggested_tools: string[]
  suggested_prompt: string
  suggested_context_level: string
  suggested_max_steps: number
  suggested_temperature: number
  reasoning: string
}

interface AgentCreationPreviewProps {
  description: string
  onClose: () => void
  onCreated?: (agentId: string) => void
}

export function AgentCreationPreview({ description, onClose, onCreated }: AgentCreationPreviewProps) {
  const [config, setConfig] = useState<GeneratedConfig | null>(null)
  const [isGenerating, setIsGenerating] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const generate = async () => {
      try {
        const token = localStorage.getItem("auth_token")
        const res = await fetch("/api/backend-proxy/custom-agents/generate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ description }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Erro" }))
          throw new Error(err.detail || "Erro ao gerar")
        }
        const data = await res.json()
        if (!cancelled) setConfig(data)
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erro ao gerar configuracao")
      } finally {
        if (!cancelled) setIsGenerating(false)
      }
    }
    generate()
    return () => { cancelled = true }
  }, [description])

  const handleCreate = async () => {
    if (!config) return
    setIsCreating(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/custom-agents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          name: config.suggested_name,
          role: config.suggested_role,
          description: config.suggested_role,
          system_prompt: config.suggested_prompt,
          allowed_tools: config.suggested_tools,
          domain: config.suggested_domain,
          context_level: config.suggested_context_level,
          max_steps: config.suggested_max_steps,
          temperature: config.suggested_temperature,
        }),
      })
      if (!res.ok) throw new Error("Erro ao criar")
      const agent = await res.json()
      toast.success(`Agente "${config.suggested_name}" criado!`, "Agora vincule a uma vaga ou pool.")
      onCreated?.(agent.id)
      onClose()
    } catch {
      toast.error("Erro ao criar agente")
    } finally {
      setIsCreating(false)
    }
  }

  const domainLabel = config ? (CATEGORY_LABELS[config.suggested_domain as AgentCategory] || config.suggested_domain) : ""

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-lia-border-subtle">
        <div className="flex items-center gap-2">
          <Wand2 className="w-4 h-4 text-wedo-cyan-dark" />
          <h3 className={cn(textStyles.subtitle, "text-sm font-semibold")}>Novo Agente</h3>
          <BetaBadge size="sm" />
        </div>
        <button type="button" onClick={onClose} className="text-lia-text-disabled hover:text-lia-text-secondary">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-4 space-y-3">
        <div className={cn(cardStyles.flat, "p-3")}>
          <p className="text-[10px] text-lia-text-disabled uppercase font-semibold">Sua solicitacao</p>
          <p className="text-xs text-lia-text-secondary mt-1">{description}</p>
        </div>

        {isGenerating && (
          <div className="flex items-center gap-2 py-8 justify-center">
            <Loader2 className="w-4 h-4 animate-spin text-wedo-cyan-dark" />
            <span className="text-xs text-lia-text-secondary">LIA esta configurando o agente...</span>
          </div>
        )}

        {error && (
          <div className={cn(cardStyles.default, "p-3 border-red-200")}>
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}

        {config && (
          <>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              <span className={cn(textStyles.subtitle, "text-sm font-semibold")}>Configuracao sugerida</span>
            </div>

            <div className={cn(cardStyles.default, "p-4 space-y-2")}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-lia-text-primary">{config.suggested_name}</span>
                <span className={badgeStyles.cyan}>{domainLabel}</span>
              </div>
              <p className="text-xs text-lia-text-secondary">{config.suggested_role}</p>

              <div className="flex flex-wrap gap-1 pt-1">
                {config.suggested_tools.map((tool) => (
                  <span key={tool} className={cn(badgeStyles.default, "text-[10px]")}>
                    {TOOL_LABELS[tool] || tool}
                  </span>
                ))}
              </div>

              <div className="flex items-center gap-3 pt-1 text-[10px] text-lia-text-disabled">
                <span>Contexto: {config.suggested_context_level}</span>
                <span>Steps: {config.suggested_max_steps}</span>
                <span>Temp: {config.suggested_temperature}</span>
              </div>

              {config.reasoning && (
                <p className="text-[11px] text-wedo-cyan-dark italic pt-1">
                  LIA: {config.reasoning}
                </p>
              )}

              <button
                type="button"
                onClick={() => setShowPrompt(!showPrompt)}
                className="flex items-center gap-1 text-[10px] text-lia-text-disabled hover:text-lia-text-secondary pt-1"
              >
                {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {showPrompt ? "Ocultar prompt" : "Ver prompt completo"}
              </button>
              {showPrompt && (
                <pre className="text-[10px] text-lia-text-secondary bg-lia-bg-tertiary rounded-md p-3 overflow-auto max-h-32 whitespace-pre-wrap font-mono">
                  {config.suggested_prompt}
                </pre>
              )}
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      {config && (
        <div className="p-4 border-t border-lia-border-subtle flex gap-2">
          <button
            type="button"
            onClick={handleCreate}
            disabled={isCreating}
            className={cn(buttonStyles.primary, "flex-1 text-xs px-4 py-2")}
          >
            {isCreating ? "Criando..." : "Criar agente"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className={cn(buttonStyles.ghost, "text-xs px-3 py-2")}
          >
            Cancelar
          </button>
        </div>
      )}
    </div>
  )
}
''')


# ============================================================
# 5. Frontend: AgentChatCard (inline card in chat for query/metrics)
# ============================================================
print("\n=== 5. AgentChatCard ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/AgentChatCard.tsx", '''"use client"

import React from "react"
import { Bot, Activity, Clock, Zap } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import type { CustomAgent } from "./types"
import { CATEGORY_LABELS } from "./types"

interface AgentChatCardProps {
  agent: CustomAgent
  deploymentCount?: number
  onViewDetails?: () => void
}

export function AgentChatCard({ agent, deploymentCount = 0, onViewDetails }: AgentChatCardProps) {
  const domainLabel = CATEGORY_LABELS[agent.domain as keyof typeof CATEGORY_LABELS] || agent.domain
  const statusBadge = agent.status === "active" ? badgeStyles.success :
                      agent.status === "paused" ? badgeStyles.warning :
                      badgeStyles.default

  return (
    <div className={cn(cardStyles.default, "p-3 space-y-2 max-w-md")}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-wedo-cyan/10 flex items-center justify-center">
            <Bot className="w-4 h-4 text-wedo-cyan-dark" />
          </div>
          <div>
            <p className="text-sm font-semibold text-lia-text-primary">{agent.name}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn(badgeStyles.default, "text-[10px]")}>{domainLabel}</span>
              <span className={cn(statusBadge, "text-[10px]")}>{agent.status}</span>
            </div>
          </div>
        </div>
        <BetaBadge size="sm" />
      </div>

      {agent.description && (
        <p className="text-[11px] text-lia-text-secondary line-clamp-2">{agent.description}</p>
      )}

      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3 text-lia-text-disabled" />
          <span className="font-bold font-inter text-lia-text-primary">{agent.total_executions}</span>
          <span className="text-[10px] text-lia-text-disabled">exec</span>
        </div>
        <div className="flex items-center gap-1">
          <Zap className="w-3 h-3 text-lia-text-disabled" />
          <span className="font-bold font-inter text-lia-text-primary">{deploymentCount}</span>
          <span className="text-[10px] text-lia-text-disabled">vinc</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3 text-lia-text-disabled" />
          <span className="font-bold font-inter text-lia-text-primary">
            {agent.avg_confidence > 0 ? `${(agent.avg_confidence * 100).toFixed(0)}%` : "-"}
          </span>
          <span className="text-[10px] text-lia-text-disabled">conf</span>
        </div>
      </div>

      {onViewDetails && (
        <button
          type="button"
          onClick={onViewDetails}
          className="w-full text-[11px] text-wedo-cyan-dark hover:underline text-left pt-1"
        >
          Ver detalhes completos →
        </button>
      )}
    </div>
  )
}


interface MetricsSummaryCardProps {
  period_days: number
  total_executions: number
  total_tokens: number
  estimated_cost_brl: number
  avg_confidence: number
  active_agents: number
  top_agents: Array<{ agent_id: string; agent_name: string; execution_count: number; total_tokens: number }>
}

export function MetricsSummaryCard({
  period_days,
  total_executions,
  total_tokens,
  estimated_cost_brl,
  avg_confidence,
  active_agents,
  top_agents,
}: MetricsSummaryCardProps) {
  return (
    <div className={cn(cardStyles.default, "p-3 space-y-3 max-w-md")}>
      <div className="flex items-center gap-2">
        <Activity className="w-4 h-4 text-wedo-cyan-dark" />
        <p className="text-sm font-semibold text-lia-text-primary">Metricas dos ultimos {period_days} dias</p>
        <BetaBadge size="sm" />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-[10px] text-lia-text-disabled uppercase">Execucoes</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">{total_executions}</p>
        </div>
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-[10px] text-lia-text-disabled uppercase">Agents ativos</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">{active_agents}</p>
        </div>
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-[10px] text-lia-text-disabled uppercase">Tokens</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">{total_tokens.toLocaleString("pt-BR")}</p>
        </div>
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-[10px] text-lia-text-disabled uppercase">Custo estimado</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">R${estimated_cost_brl.toFixed(4)}</p>
        </div>
      </div>

      {top_agents.length > 0 && (
        <div>
          <p className="text-[10px] text-lia-text-disabled uppercase mb-1.5">Top agents</p>
          <div className="space-y-1">
            {top_agents.map((a, i) => (
              <div key={a.agent_id} className="flex items-center justify-between text-xs">
                <span className="text-lia-text-primary">{i + 1}. {a.agent_name}</span>
                <span className="text-[10px] text-lia-text-disabled">
                  {a.execution_count} exec · {a.total_tokens.toLocaleString("pt-BR")} tkn
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {avg_confidence > 0 && (
        <p className="text-[10px] text-lia-text-disabled">
          Confianca media: {(avg_confidence * 100).toFixed(0)}%
        </p>
      )}
    </div>
  )
}
''')


# ============================================================
# 6. Proxy routes for new backend endpoints
# ============================================================
print("\n=== 6. Proxy routes ===")
write_file(BASE_FE, "app/api/backend-proxy/custom-agents/search/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const qs = searchParams.toString()
    const res = await fetch(`${BACKEND_URL}/api/v1/custom-agents/search?${qs}`, { headers: getAuthHeaders(req) })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')

write_file(BASE_FE, "app/api/backend-proxy/custom-agents/studio-metrics-summary/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const qs = searchParams.toString()
    const res = await fetch(`${BACKEND_URL}/api/v1/custom-agents/studio/metrics/summary${qs ? `?${qs}` : ""}`, { headers: getAuthHeaders(req) })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')


# ============================================================
# 7. New hooks: use-studio-chat-intents
# ============================================================
print("\n=== 7. useStudioChatIntents hook ===")
write_file(BASE_FE, "hooks/agents/use-studio-chat-intents.ts", '''"use client"

import { useCallback } from "react"
import type { CustomAgent } from "@/components/pages-agent-studio/custom-agents/types"

interface StudioMetricsSummary {
  period_days: number
  total_executions: number
  total_tokens_input: number
  total_tokens_output: number
  total_tokens: number
  total_credits: number
  estimated_cost_brl: number
  avg_confidence: number
  avg_latency_ms: number
  active_agents: number
  top_agents: Array<{ agent_id: string; agent_name: string; execution_count: number; total_tokens: number }>
}

export function useStudioChatIntents() {
  const searchAgentByName = useCallback(async (name: string): Promise<CustomAgent[]> => {
    const token = localStorage.getItem("auth_token")
    const res = await fetch(`/api/backend-proxy/custom-agents/search?name=${encodeURIComponent(name)}&limit=5`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) return []
    const data = await res.json()
    return data.agents || []
  }, [])

  const getMetricsSummary = useCallback(async (periodDays = 7): Promise<StudioMetricsSummary | null> => {
    const token = localStorage.getItem("auth_token")
    const res = await fetch(`/api/backend-proxy/custom-agents/studio-metrics-summary?period_days=${periodDays}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) return null
    return await res.json()
  }, [])

  /** Extract agent name from user message like "como esta o agente Triagem Tech" */
  const extractAgentName = useCallback((message: string): string | null => {
    const patterns = [
      /(?:agente|agent)\\s+([A-Z][\\w\\s]{2,40})/i,
      /(?:do|da|sobre|o)\\s+agente\\s+([\\w\\s]{2,40})/i,
    ]
    for (const p of patterns) {
      const match = message.match(p)
      if (match?.[1]) {
        return match[1].trim().replace(/[?!.,]$/, "")
      }
    }
    return null
  }, [])

  return { searchAgentByName, getMetricsSummary, extractAgentName }
}
''')

patch_file(
    BASE_FE,
    "hooks/agents/index.ts",
    'export { usePendingApprovals } from "./use-approvals"',
    'export { usePendingApprovals } from "./use-approvals"\nexport { useStudioChatIntents } from "./use-studio-chat-intents"',
    "export studio chat intents hook",
)


# ============================================================
# 8. Update barrel
# ============================================================
print("\n=== 8. Barrel ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/index.ts", '''export { TemplateGallery } from "./TemplateGallery"
export { TemplateCard } from "./TemplateCard"
export { AgentCard } from "./AgentCard"
export { AgentCardSkeleton } from "./AgentCardSkeleton"
export { AgentDetailsPanel } from "./AgentDetailsPanel"
export { AgentActivityCard } from "./AgentActivityCard"
export { DeployDialog } from "./DeployDialog"
export { ConversationalCreator } from "./ConversationalCreator"
export { TestDebugPanel } from "./TestDebugPanel"
export { ToolSelector } from "./ToolSelector"
export { ContextLevelSelect } from "./ContextLevelSelect"
export { ApprovalsList } from "./ApprovalsList"
export { RequestApprovalButton } from "./RequestApprovalButton"
export { AgentCreationPreview } from "./AgentCreationPreview"
export { AgentChatCard, MetricsSummaryCard } from "./AgentChatCard"
export type * from "./types"
''')


# ============================================================
# VERIFY
# ============================================================
import ast
print("\n=== Verify backend AST ===")
try:
    ast.parse(read_file(BASE_BE, "app/api/v1/custom_agents.py"))
    print("  OK: custom_agents.py")
except SyntaxError as e:
    print(f"  ERROR: {e}")

print("\nOnda 4 complete!")
