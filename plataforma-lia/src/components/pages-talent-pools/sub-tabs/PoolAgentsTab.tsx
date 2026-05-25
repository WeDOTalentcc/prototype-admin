"use client"

/**
 * PoolAgentsTab — Sprint 7B-2 (substitui RealAgentsTab Studio dentro de pools).
 *
 * Consome foundation 7B-1:
 *   - usePoolAgents(poolId): SWR assignments
 *   - useDispatchAgent / useUpdateAssignment / useUnassignAgent: mutations
 *
 * Pattern canonical:
 *   - Filter chips por categoria (All + 5 categorias canonical)
 *   - Cards de assignment com category badge neutra DS (sem cyan — Sprint 2 cleanup)
 *   - Loading skeleton explícito
 *   - Error explicit + retry
 *   - Empty state UI canonical
 *
 * NÃO toca AgentsTab Studio (refactor é 7B-3).
 */
import React, { useState, useMemo } from "react"
import { Plus, Play, Pause, Trash2, Settings2, AlertCircle, Loader2, Bot } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { textStyles, cardStyles, buttonStyles } from "@/lib/design-tokens"
import {
  usePoolAgents,
  useDispatchAgent,
  useUpdateAssignment,
  useUnassignAgent,
} from "@/hooks/talent-pools/use-pool-agents"
import type { PoolAgentAssignment } from "@/types/pool-agent-assignment"
import { AssignAgentModal } from "../AssignAgentModal"
import { ConfigureAssignmentModal } from "../ConfigureAssignmentModal"

type CategoryFilter = "all" | "sourcing" | "screening" | "communication" | "analytics" | "automation"

const CATEGORY_OPTIONS: { value: CategoryFilter; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "sourcing", label: "Sourcing" },
  { value: "screening", label: "Screening" },
  { value: "communication", label: "Comunicação" },
  { value: "analytics", label: "Analytics" },
  { value: "automation", label: "Automação" },
]

const STATUS_LABELS: Record<string, string> = {
  active: "Ativo",
  paused: "Pausado",
  completed: "Concluído",
  error: "Erro",
}

function formatLastRun(iso: string | null): string {
  if (!iso) return "Nunca executado"
  try {
    const d = new Date(iso)
    return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })
  } catch {
    return "—"
  }
}

interface PoolAgentsTabProps {
  poolId: string
}

export function PoolAgentsTab({ poolId }: PoolAgentsTabProps) {
  const { data: assignments, isLoading, error, mutate } = usePoolAgents(poolId)
  const dispatchAgent = useDispatchAgent({ poolId })
  const updateAssignment = useUpdateAssignment({ poolId })
  const unassignAgent = useUnassignAgent({ poolId })

  const [filter, setFilter] = useState<CategoryFilter>("all")
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [configuring, setConfiguring] = useState<PoolAgentAssignment | null>(null)

  const filtered = useMemo(() => {
    if (filter === "all") return assignments
    return assignments.filter((a) => a.custom_agent_category === filter)
  }, [assignments, filter])

  const handleDispatch = async (id: string) => {
    try {
      await dispatchAgent(id)
    } catch (e) {
      console.error("[PoolAgentsTab] dispatch failed", e)
    }
  }

  const handleToggleStatus = async (a: PoolAgentAssignment) => {
    const nextStatus = a.status === "active" ? "paused" : "active"
    try {
      await updateAssignment(a.id, { status: nextStatus as "active" | "paused" })
    } catch (e) {
      console.error("[PoolAgentsTab] toggle failed", e)
    }
  }

  const handleRemove = async (id: string) => {
    if (!window.confirm("Remover este agente do pool? Esta ação não pode ser desfeita.")) return
    try {
      await unassignAgent(id)
    } catch (e) {
      console.error("[PoolAgentsTab] unassign failed", e)
    }
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <AlertCircle className="w-8 h-8 text-red-500" />
        <p className={textStyles.body}>Erro ao carregar agentes: {error}</p>
        <Button variant="outline" onClick={() => mutate()}>
          Tentar novamente
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header: filter chips + add button */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap" role="group" aria-label="Filtrar agentes por categoria">
          {CATEGORY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              data-testid={`filter-chip-${opt.value}`}
              onClick={() => setFilter(opt.value)}
              className={
                filter === opt.value
                  ? "px-3 py-1.5 text-sm rounded-full border border-lia-border bg-lia-surface-strong text-lia-text-primary font-medium"
                  : "px-3 py-1.5 text-sm rounded-full border border-lia-border-subtle bg-lia-surface text-lia-text-secondary hover:text-lia-text-primary hover:border-lia-border transition-colors"
              }
            >
              {opt.label}
            </button>
          ))}
        </div>
        <Button
          onClick={() => setShowAssignModal(true)}
          data-testid="add-agent-btn"
          className={buttonStyles.primary}
        >
          <Plus className="w-4 h-4 mr-1" />
          Adicionar agente
        </Button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-2" data-testid="pool-agents-loading">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-lia-surface-muted animate-pulse rounded-md" />
          ))}
        </div>
      )}

      {/* Empty */}
      {!isLoading && filtered.length === 0 && (
        <Card className={cardStyles.default}>
          <CardContent className="py-12 flex flex-col items-center text-center gap-3" data-testid="pool-agents-empty">
            <Bot className="w-10 h-10 text-lia-text-tertiary" />
            <p className={textStyles.body}>
              {filter === "all"
                ? "Nenhum agente atribuído. Clique em + Adicionar agente."
                : `Nenhum agente nesta categoria. Tente outro filtro ou adicione um novo.`}
            </p>
          </CardContent>
        </Card>
      )}

      {/* List */}
      {!isLoading && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((a) => (
            <Card key={a.id} className={cardStyles.default} data-testid={`assignment-card-${a.id}`}>
              <CardContent className="p-4 flex items-center justify-between gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={textStyles.h4}>{a.custom_agent_name || "(sem nome)"}</span>
                    {a.custom_agent_category && (
                      <Chip variant="neutral" muted>
                        {a.custom_agent_category}
                      </Chip>
                    )}
                    <Chip variant={a.status === "active" ? "success" : "neutral"} muted>
                      {STATUS_LABELS[a.status] ?? a.status}
                    </Chip>
                  </div>
                  <p className={textStyles.bodySmall + " mt-1 text-lia-text-secondary"}>
                    Última execução: {formatLastRun(a.last_run_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    data-testid={`assignment-run-${a.id}`}
                    onClick={() => handleDispatch(a.id)}
                    className={buttonStyles.outline}
                    title="Rodar agora"
                  >
                    <Play className="w-4 h-4 mr-1" />
                    Rodar
                  </button>
                  <button
                    type="button"
                    data-testid={`assignment-toggle-status-${a.id}`}
                    onClick={() => handleToggleStatus(a)}
                    className={buttonStyles.outline}
                    title={a.status === "active" ? "Pausar" : "Ativar"}
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    data-testid={`assignment-configure-${a.id}`}
                    onClick={() => setConfiguring(a)}
                    className={buttonStyles.outline}
                    title="Configurar"
                  >
                    <Settings2 className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    data-testid={`assignment-remove-${a.id}`}
                    onClick={() => handleRemove(a.id)}
                    className={buttonStyles.outline}
                    title="Remover"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modals */}
      {showAssignModal && (
        <AssignAgentModal
          poolId={poolId}
          open={showAssignModal}
          initialCategory={filter !== "all" ? filter : undefined}
          onClose={() => setShowAssignModal(false)}
          onAssigned={() => {
            setShowAssignModal(false)
            mutate()
          }}
        />
      )}
      {configuring && (
        <ConfigureAssignmentModal
          assignment={configuring}
          poolId={poolId}
          open={!!configuring}
          onClose={() => setConfiguring(null)}
          onSaved={() => {
            setConfiguring(null)
            mutate()
          }}
        />
      )}
    </div>
  )
}
