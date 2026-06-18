"use client"

import React, { useState, useEffect, useCallback } from"react"
import {
  Users, Search, Bot, Settings, Plus, ArrowRight, Heart,
  Eye, Mail, MoreHorizontal, ChevronDown, Filter,
  Briefcase, Pause, Play, Archive, Pencil, Trash2, Check, X, Loader2
} from"lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from"@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Progress } from"@/components/ui/progress"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from"@/components/ui/dialog"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from"@/components/ui/dropdown-menu"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles,
  tabStyles, actionButtonStyles
} from"@/lib/design-tokens"
import CandidateOriginBadge from"@/components/pages-agent-studio/CandidateOriginBadge"
import VoiceScreeningButton from"@/components/pages-agent-studio/VoiceScreeningButton"
import SourcingTab from "./sub-tabs/sourcing-tab"
import { useActiveAgentsSummary } from "@/hooks/agents/use-active-agents-summary"

// ---------- Types ----------

interface TalentPool {
  id: string
  name: string
  description: string
  status:"active" |"paused" |"archived"
  ideal_profile_id: string | null
  ideal_profile_name: string | null
  agent_sourcing_enabled: boolean
  screening_approved: boolean
  candidates_count: number
  screened_count: number
  ready_count: number
  created_by: string
  created_at: string
}

interface PoolCandidate {
  id: string
  stage:"discovered" |"contacted" |"screening" |"screened" |"ready"
  origin:"agent" |"manual" |"import" |"search"
  fit_score: number | null
  notes: string | null
  moved_to_job_id: number | null
  screening_data: Record<string, unknown>
  match_criteria: Record<string, unknown>
  created_at?: string
  candidate: {
    id: number
    name: string
    email: string
    current_company: string | null
    role_name: string | null
    seniority_level: string | null
    city: string | null
    state: string | null
    avatar_url: string | null
    technical_skills: string[]
    years_of_experience: number | null
  }
}

// ---------- Constants ----------

const STAGES = [
  { id:"discovered", label:"Descoberto", icon:"🔍", color:"bg-lia-bg-tertiary text-lia-text-secondary" },
  { id:"contacted", label:"Contatado", icon:"📧", color:"bg-blue-100 text-blue-700" },
  { id:"screening", label:"Em triagem", icon:"🔄", color:"bg-yellow-100 text-yellow-700" },
  { id:"screened", label:"Triado", icon:"✅", color:"bg-green-100 text-green-700" },
  { id:"ready", label:"Pronto", icon:"🎯", color:"bg-purple-100 text-purple-700" },
] as const

const ORIGIN_ICONS: Record<string, { icon: string; label: string }> = {
  agent: { icon:"🤖", label:"Sourciado pelo Agente" },
  manual: { icon:"👤", label:"Adicionado manualmente" },
  import: { icon:"📥", label:"Importado" },
  search: { icon:"🔍", label:"Via busca" },
}

const TABS = [
  { id:"candidates", label:"Candidatos", icon: Users },
  { id:"sourcing", label:"Captação", icon: Search },
  { id:"agents", label:"Agentes", icon: Bot },
  { id:"config", label:"Configurações", icon: Settings },
] as const

// ---------- Stage Progress Component ----------

function StageProgress({ stage }: { stage: string }) {
  const stageIdx = STAGES.findIndex(s => s.id === stage)
  const progress = ((stageIdx + 1) / STAGES.length) * 100

  return (
    <div className="flex items-center gap-1.5" title={STAGES[stageIdx]?.label}>
      {STAGES.map((s, i) => (
        <div
          key={s.id}
          className={`w-2 h-2 rounded-full ${
            i <= stageIdx ?"bg-lia-bg-inverse" :"bg-lia-interactive-active"
          }`}
          title={s.label}
        />
      ))}
    </div>
  )
}

// ---------- Main Component ----------

interface TalentPoolPageProps {
  poolId: string
  onNavigateToJob?: (jobId: number) => void
  onOpenCandidate?: (candidateId: number) => void
}

export default function TalentPoolPage({
  poolId,
  onNavigateToJob,
  onOpenCandidate,
}: TalentPoolPageProps) {
  const [pool, setPool] = useState<TalentPool | null>(null)
  const [candidates, setCandidates] = useState<PoolCandidate[]>([])
  const [activeTab, setActiveTab] = useState("candidates")
  // Onda 2 F6 — pingo cyan na aba "Agentes" quando ha agente rodando neste pool.
  const { data: poolAgentSummary } = useActiveAgentsSummary({
    surface: "pool",
    limit: 20,
  })
  const hasRunningPoolAgent = (poolAgentSummary?.items ?? []).some(
    (item) =>
      item.target_type === "talent_pool" &&
      item.target_id === poolId &&
      item.status === "running",
  )
  const [stageFilter, setStageFilter] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [showMoveModal, setShowMoveModal] = useState(false)
  const [isCreatingJob, setIsCreatingJob] = useState(false)
  const [showArchiveModal, setShowArchiveModal] = useState(false)

  // Fase 2 F2 — ponte in-page para LIA via apply_table_state surface=talent_pool.
  useEffect(() => {
    function handleApplyTableState(e: Event) {
      const { surface, patch } = (
        e as CustomEvent<{ surface: string; patch: { stage?: string | null; poolTab?: string } }>
      ).detail ?? {}
      if (surface !== "talent_pool" || !patch) return
      if ("stage" in patch) setStageFilter(patch.stage ?? null)
      if (typeof patch.poolTab === "string") setActiveTab(patch.poolTab)
    }
    window.addEventListener("lia:apply_table_state", handleApplyTableState)
    return () => window.removeEventListener("lia:apply_table_state", handleApplyTableState)
  }, [])

  // Load pool data
  const loadPool = useCallback(async () => {
    try {
      const res = await fetch(`/api/backend-proxy/talent-pools/${poolId}`)
      const data = await res.json()
      setPool(data?.data?.attributes || data)
    } catch (err) {
      console.error("Failed to load pool:", err)
    }
  }, [poolId])

  const loadCandidates = useCallback(async () => {
    try {
      setIsLoading(true)
      const stageParam = stageFilter ? `?stage=${stageFilter}` :""
      const res = await fetch(`/api/backend-proxy/talent-pools/${poolId}/candidates${stageParam}`)
      const data = await res.json()
      setCandidates(data?.data?.map((d: { attributes: PoolCandidate }) => d.attributes) || [])
    } catch (err) {
      console.error("Failed to load candidates:", err)
    } finally {
      setIsLoading(false)
    }
  }, [poolId, stageFilter])

  useEffect(() => { loadPool() }, [loadPool])
  useEffect(() => { loadCandidates() }, [loadCandidates])

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) { next.delete(id) } else { next.add(id) }
      return next
    })
  }

  const selectAll = () => {
    if (selectedIds.size === candidates.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(candidates.map(c => c.id)))
    }
  }

  const createJobFromPool = async () => {
    if (!pool?.ideal_profile_id) return
    setIsCreatingJob(true)
    try {
      const res = await fetch(`/api/backend-proxy/talent-pools/${poolId}/create-job`, {
        method:"POST",
        headers: {"Content-Type":"application/json" },
      })
      const data = await res.json()
      if (data?.job_id && onNavigateToJob) onNavigateToJob(data.job_id)
    } catch (err) {
      console.error("Failed to create job:", err)
    } finally {
      setIsCreatingJob(false)
    }
  }

  const togglePoolStatus = async () => {
    if (!pool) return
    const newStatus = pool.status ==="active" ?"paused" :"active"
    try {
      await fetch(`/api/backend-proxy/talent-pools/${poolId}`, {
        method:"PATCH",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({ talent_pool: { status: newStatus } }),
      })
      loadPool()
    } catch (err) {
      console.error("Failed to toggle status:", err)
    }
  }

  if (!pool) return null

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className={textStyles.titleLarge}>{pool.name}</h1>
            {pool.description && (
              <p className={`${textStyles.description} mt-1`}>{pool.description}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Chip variant={pool.status ==="active" ? "success" : "warning"}>
              {pool.status ==="active" ?"Ativo" : pool.status ==="paused" ?"Pausado" :"Arquivado"}
            </Chip>
            {pool.ideal_profile_name && (
              <span className={textStyles.caption}>Arquétipo: {pool.ideal_profile_name}</span>
            )}
            <Button
              className={buttonStyles.outline}
              onClick={togglePoolStatus}
              title={pool.status ==="active" ?"Pausar banco" :"Reativar banco"}
            >
              {pool.status ==="active" ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
            {pool.ideal_profile_id && (
              <Button
                className={buttonStyles.primary}
                onClick={createJobFromPool}
                disabled={isCreatingJob}
              >
                <Briefcase className="w-4 h-4 mr-1" />
                {isCreatingJob ?"Criando..." :"Criar Vaga"}
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button className={buttonStyles.outline} title="Mais opções">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => setActiveTab("config")}>
                  <Pencil className="w-4 h-4 mr-2" />
                  Editar banco
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-red-600 focus:text-red-600"
                  onClick={() => setShowArchiveModal(true)}
                >
                  <Archive className="w-4 h-4 mr-2" />
                  Arquivar banco
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Summary cards */}
        <div className="flex gap-4 mt-4">
          <Card className={`${cardStyles.flat} flex-1`}>
            <CardContent className="p-3 text-center">
              <p className={textStyles.metricLarge}>{pool.candidates_count}</p>
              <p className={textStyles.caption}>Total</p>
            </CardContent>
          </Card>
          <Card className={`${cardStyles.flat} flex-1`}>
            <CardContent className="p-3 text-center">
              <p className={textStyles.metricLarge}>{pool.screened_count}</p>
              <p className={textStyles.caption}>Triados</p>
            </CardContent>
          </Card>
          <Card className={`${cardStyles.flat} flex-1`}>
            <CardContent className="p-3 text-center">
              <p className={textStyles.metricLarge}>{pool.ready_count}</p>
              <p className={textStyles.caption}>Prontos</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex-shrink-0 px-6 pt-3">
        <div className={tabStyles.pillContainer}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
            >
              <tab.icon className={tabStyles.pillIcon} />
              {tab.label}
              {/* Onda 2 F6 — pingo cyan na aba "Agentes" quando ha agente rodando neste pool. */}
              {tab.id === "agents" && hasRunningPoolAgent && (
                <span
                  className="ml-1 w-1.5 h-1.5 rounded-full bg-wedo-cyan inline-block"
                  aria-label="Agente em execucao neste pool"
                  title="Agente trabalhando agora neste pool"
                  role="img"
                />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden px-6 py-4">
        {activeTab ==="candidates" && (
          <CandidatesTab
            candidates={candidates}
            stageFilter={stageFilter}
            setStageFilter={setStageFilter}
            selectedIds={selectedIds}
            toggleSelect={toggleSelect}
            selectAll={selectAll}
            isLoading={isLoading}
            onOpenCandidate={onOpenCandidate}
            onMoveToJob={() => setShowMoveModal(true)}
          />
        )}

        {activeTab ==="sourcing" && (
          <SourcingTab
            poolId={poolId}
            idealProfileId={pool.ideal_profile_id}
            onAddToPool={() => { loadCandidates(); loadPool() }}
          />
        )}

        {activeTab ==="agents" && (
          <AgentsTabWrapper pool={pool} />
        )}

        {activeTab ==="config" && (
          <ConfigTab pool={pool} onUpdate={loadPool} />
        )}
      </div>

      {/* Move to Job Modal */}
      {showMoveModal && (
        <MoveToJobModal
          poolId={poolId}
          selectedIds={Array.from(selectedIds)}
          candidates={candidates.filter(c => selectedIds.has(c.id))}
          onClose={() => setShowMoveModal(false)}
          onMoved={(jobId) => {
            setShowMoveModal(false)
            setSelectedIds(new Set())
            loadCandidates()
            loadPool()
            if (onNavigateToJob) onNavigateToJob(jobId)
          }}
        />
      )}

      {/* Archive Confirmation Modal */}
      {showArchiveModal && (
        <ArchivePoolModal
          poolName={pool.name}
          poolId={poolId}
          onClose={() => setShowArchiveModal(false)}
          onArchived={() => {
            setShowArchiveModal(false)
            window.dispatchEvent(new CustomEvent("lia:talent-pool-archived", { detail: { poolId } }))
            window.history.back()
          }}
        />
      )}
    </div>
  )
}

// ---------- Candidates Tab ----------

interface CandidatesTabProps {
  candidates: PoolCandidate[]
  stageFilter: string | null
  setStageFilter: (stage: string | null) => void
  selectedIds: Set<string>
  toggleSelect: (id: string) => void
  selectAll: () => void
  isLoading: boolean
  onOpenCandidate?: (id: number) => void
  onMoveToJob: () => void
}

function CandidatesTab({
  candidates, stageFilter, setStageFilter, selectedIds,
  toggleSelect, selectAll, isLoading, onOpenCandidate, onMoveToJob,
}: CandidatesTabProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-lia-text-tertiary" />
          <button
            onClick={() => setStageFilter(null)}
            className={`text-sm px-2 py-1 rounded ${!stageFilter ?"bg-lia-bg-inverse text-white" :"text-lia-text-secondary hover:bg-lia-bg-tertiary"}`}
          >
            Todos
          </button>
          {STAGES.map(s => (
            <button
              key={s.id}
              onClick={() => setStageFilter(s.id)}
              className={`text-sm px-2 py-1 rounded ${stageFilter === s.id ?"bg-lia-bg-inverse text-white" :"text-lia-text-secondary hover:bg-lia-bg-tertiary"}`}
            >
              {s.icon} {s.label}
            </button>
          ))}
        </div>

        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2">
            <span className={textStyles.caption}>{selectedIds.size} selecionados</span>
            <Button className={buttonStyles.primary} onClick={onMoveToJob}>
              <ArrowRight className="w-4 h-4 mr-1" />
              Mover para Vaga
            </Button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-lia-border-subtle">
              <th className="py-2 px-3 text-left w-8">
                <input
                  type="checkbox"
                  checked={selectedIds.size === candidates.length && candidates.length > 0}
                  onChange={selectAll}
                  className="rounded border-lia-border-default"
                />
              </th>
              <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>Candidato</th>
              <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}> Nota</th>
              <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>Status</th>
              <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>Progresso</th>
              <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>Origem</th>
              <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>Ações</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={7} className="py-8 text-center text-lia-text-tertiary">Carregando...</td></tr>
            ) : candidates.length === 0 ? (
              <tr><td colSpan={7} className="py-8 text-center text-lia-text-tertiary">Nenhum candidato neste banco</td></tr>
            ) : (
              candidates.map(tpc => {
                const c = tpc.candidate
                const stage = STAGES.find(s => s.id === tpc.stage)
                const origin = ORIGIN_ICONS[tpc.origin]

                return (
                  <tr
                    key={tpc.id}
                    className="hover:bg-lia-bg-secondary transition-colors"
                  >
                    <td className="py-3 px-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(tpc.id)}
                        onChange={() => toggleSelect(tpc.id)}
                        className="rounded border-lia-border-default"
                      />
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-3">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={c.avatar_url || undefined} />
                          <AvatarFallback>{c.name?.charAt(0) ||"?"}</AvatarFallback>
                        </Avatar>
                        <div>
                          <button
                            onClick={() => { if (onOpenCandidate) onOpenCandidate(c.id) }}
                            className={`${textStyles.body} font-medium hover:underline cursor-pointer`}
                          >
                            {c.name}
                          </button>
                          <p className={textStyles.caption}>
                            {[c.role_name, c.current_company].filter(Boolean).join(" ·")}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      {tpc.fit_score != null ? (
                        <span className={textStyles.body}>{tpc.fit_score}%</span>
                      ) : (
                        <span className="text-lia-text-disabled">—</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      {stage && (
                        <Chip variant="neutral" className={stage.color} title={stage.label}>
                          {stage.icon} {stage.label}
                        </Chip>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <StageProgress stage={tpc.stage} />
                    </td>
                    <td className="py-3 px-3">
                      <CandidateOriginBadge
                        origin={tpc.origin as"agent" |"manual" |"import" |"search"}
                        detail={tpc.origin ==="agent" ?"Agente Sourcing" : undefined}
                        date={tpc.created_at}
                        size="sm"
                      />
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1">
                        {tpc.stage ==="ready" && (
                          <button
                            className={actionButtonStyles.smPrimary}
                            title="Mover para Vaga"
                            onClick={() => {/* handled via selection + batch move */}}
                          >
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          className={actionButtonStyles.smOutline}
                          title="Enviar mensagem"
                        >
                          <Mail className="w-3.5 h-3.5" />
                        </button>
                        <button
                          className={actionButtonStyles.smOutline}
                          title="Ver perfil"
                          onClick={() => { if (onOpenCandidate) onOpenCandidate(c.id) }}
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------- Agents Tab — Sprint 7B-2 canonical (pool-scoped, M2M) ----------

import { PoolAgentsTab } from "./sub-tabs/PoolAgentsTab"

function AgentsTabWrapper({ pool }: { pool: TalentPool }) {
  return <PoolAgentsTab poolId={pool.id} />
}

// ---------- Config Tab ----------

function ConfigTab({ pool, onUpdate }: { pool: TalentPool; onUpdate: () => void }) {
  const [name, setName] = useState(pool.name)
  const [description, setDescription] = useState(pool.description || "")
  const [archetypes, setArchetypes] = useState<Array<{ id: string; name: string; seniority_level: string | null }>>([])
  const [selectedArchetypeId, setSelectedArchetypeId] = useState<string | null>(pool.ideal_profile_id)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [isLoadingArchetypes, setIsLoadingArchetypes] = useState(true)

  // Sync local state when pool prop changes (e.g. after external refresh)
  useEffect(() => {
    setName(pool.name)
    setDescription(pool.description || "")
    setSelectedArchetypeId(pool.ideal_profile_id)
  }, [pool.id])

  useEffect(() => {
    fetch("/api/backend-proxy/search/archetypes")
      .then(res => res.json())
      .then(data => {
        const mapped = (data?.archetypes || data?.data || []).map(
          (a: { id: string; name?: string; attributes?: { name: string; seniority_level?: string } }) => ({
            id: a.id,
            name: a.attributes?.name || a.name || "Sem nome",
            seniority_level: a.attributes?.seniority_level || null,
          })
        )
        setArchetypes(mapped)
      })
      .catch(() => {/* silently degrade — archetype select shows empty */})
      .finally(() => setIsLoadingArchetypes(false))
  }, [])

  const isDirty =
    name.trim() !== pool.name ||
    (description.trim() || "") !== (pool.description || "") ||
    selectedArchetypeId !== pool.ideal_profile_id

  const handleSave = async () => {
    if (!name.trim()) return
    setIsSaving(true)
    setSaveError(null)
    setSaveSuccess(false)
    try {
      const res = await fetch(`/api/backend-proxy/talent-pools/${pool.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          talent_pool: {
            name: name.trim(),
            description: description.trim() || null,
            ideal_profile_id: selectedArchetypeId,
          },
        }),
      })
      if (!res.ok) throw new Error("Erro ao salvar")
      setSaveSuccess(true)
      onUpdate()
      setTimeout(() => setSaveSuccess(false), 2500)
    } catch {
      setSaveError("Não foi possível salvar. Tente novamente.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    setName(pool.name)
    setDescription(pool.description || "")
    setSelectedArchetypeId(pool.ideal_profile_id)
    setSaveError(null)
  }

  return (
    <div className="space-y-5 max-w-xl">
      {/* Informações básicas */}
      <Card className={cardStyles.default}>
        <CardHeader>
          <CardTitle className={textStyles.h4}>Informações do banco</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className={`${textStyles.label} block mb-1`}>Nome *</label>
            <Input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Ex: Backend Sênior SP"
              maxLength={80}
            />
          </div>
          <div>
            <label className={`${textStyles.label} block mb-1`}>Descrição</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Objetivo deste banco de talentos..."
              rows={3}
              className="w-full border border-lia-border-default rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-gray-400 bg-transparent"
            />
          </div>
        </CardContent>
      </Card>

      {/* Arquétipo */}
      <Card className={cardStyles.default}>
        <CardHeader>
          <CardTitle className={textStyles.h4}>Arquétipo vinculado</CardTitle>
        </CardHeader>
        <CardContent>
          <p className={`${textStyles.caption} mb-3`}>
            O arquétipo gera automaticamente perguntas de triagem e critérios de avaliação WSI.
          </p>
          {isLoadingArchetypes ? (
            <p className={textStyles.caption}>Carregando arquétipos...</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              <label className="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-lia-bg-secondary">
                <input
                  type="radio"
                  name="cfg-archetype"
                  checked={selectedArchetypeId === null}
                  onChange={() => setSelectedArchetypeId(null)}
                  className="rounded-full border-lia-border-default"
                />
                <span className={textStyles.body}>Sem arquétipo</span>
              </label>
              {archetypes.map(a => (
                <label
                  key={a.id}
                  className="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-lia-bg-secondary"
                >
                  <input
                    type="radio"
                    name="cfg-archetype"
                    checked={selectedArchetypeId === a.id}
                    onChange={() => setSelectedArchetypeId(a.id)}
                    className="rounded-full border-lia-border-default"
                  />
                  <span className={textStyles.body}>{a.name}</span>
                  {a.seniority_level && (
                    <Chip variant="success">{a.seniority_level}</Chip>
                  )}
                </label>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Perguntas de triagem — read-only (gerenciado pelo agente) */}
      <Card className={cardStyles.default}>
        <CardHeader>
          <CardTitle className={textStyles.h4}>Perguntas de Triagem</CardTitle>
        </CardHeader>
        <CardContent>
          <p className={textStyles.body}>
            {pool.screening_approved ? "Aprovadas" : "Pendente de aprovação"}
          </p>
          <p className={`${textStyles.caption} mt-1`}>
            As perguntas são geradas automaticamente com base no arquétipo vinculado.
          </p>
        </CardContent>
      </Card>

      {/* Save bar */}
      {saveError && (
        <p className="text-sm text-red-600">{saveError}</p>
      )}
      <div className="flex items-center gap-3 pt-1">
        <Button
          className={buttonStyles.primary}
          onClick={handleSave}
          disabled={!isDirty || !name.trim() || isSaving}
        >
          {isSaving && <Loader2 className="w-4 h-4 mr-1 animate-spin" />}
          {isSaving ? "Salvando..." : saveSuccess ? (
            <><Check className="w-4 h-4 mr-1" />Salvo</>
          ) : "Salvar alterações"}
        </Button>
        {isDirty && !isSaving && (
          <Button className={buttonStyles.secondary} onClick={handleReset}>
            <X className="w-4 h-4 mr-1" />
            Descartar
          </Button>
        )}
      </div>
    </div>
  )
}

// ---------- Archive Pool Modal ----------

interface ArchivePoolModalProps {
  poolName: string
  poolId: string
  onClose: () => void
  onArchived: () => void
}

function ArchivePoolModal({ poolName, poolId, onClose, onArchived }: ArchivePoolModalProps) {
  const [isArchiving, setIsArchiving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleArchive = async () => {
    setIsArchiving(true)
    setError(null)
    try {
      const res = await fetch(`/api/backend-proxy/talent-pools/${poolId}`, {
        method: "DELETE",
      })
      if (!res.ok) throw new Error("Erro ao arquivar")
      onArchived()
    } catch {
      setError("Não foi possível arquivar. Tente novamente.")
      setIsArchiving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>Arquivar banco</DialogTitle>
          <DialogDescription className={`${textStyles.body} mt-1`}>
            O banco <strong>{poolName}</strong> será arquivado. Os candidatos e histórico são preservados, mas o banco não aparecerá mais como ativo.
          </DialogDescription>
        </DialogHeader>
        {error && <p className="text-sm text-red-600 px-1">{error}</p>}
        <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={onClose} disabled={isArchiving}>
            Cancelar
          </Button>
          <Button
            className={buttonStyles.destructive}
            onClick={handleArchive}
            disabled={isArchiving}
          >
            {isArchiving
              ? <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              : <Archive className="w-4 h-4 mr-1" />}
            {isArchiving ? "Arquivando..." : "Arquivar banco"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ---------- Move to Job Modal ----------

interface MoveToJobModalProps {
  poolId: string
  selectedIds: string[]
  candidates: PoolCandidate[]
  onClose: () => void
  onMoved: (jobId: number) => void
}

// ---------- Create Pool Modal ----------

interface CreatePoolModalProps {
  onClose: () => void
  onCreated: (poolId: string, poolName: string) => void
}

export function CreatePoolModal({ onClose, onCreated }: CreatePoolModalProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [archetypes, setArchetypes] = useState<Array<{ id: string; name: string; seniority_level: string | null }>>([])
  const [selectedArchetypeId, setSelectedArchetypeId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [isLoadingArchetypes, setIsLoadingArchetypes] = useState(true)

  useEffect(() => {
    fetch("/api/backend-proxy/search/archetypes")
      .then(res => res.json())
      .then(data => {
        const mapped = (data?.archetypes || data?.data || []).map(
          (a: { id: string; name?: string; attributes?: { name: string; seniority_level?: string } }) => ({
            id: a.id,
            name: a.attributes?.name || a.name ||"Sem nome",
            seniority_level: a.attributes?.seniority_level || null,
          })
        )
        setArchetypes(mapped)
      })
      .catch((err) => { console.error('[TalentPoolPage] archetypes fetch failed', err) })
      .finally(() => setIsLoadingArchetypes(false))
  }, [])

  const handleCreate = async () => {
    if (!name.trim()) return
    setIsCreating(true)
    setCreateError(null)
    try {
      const res = await fetch("/api/backend-proxy/talent-pools", {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({
          talent_pool: {
            name: name.trim(),
            description: description.trim() || null,
            ideal_profile_id: selectedArchetypeId,
          },
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setCreateError("Erro ao criar banco. Tente novamente.")
        return
      }
      const newId = data?.data?.id || data?.id
      if (newId) onCreated(newId, name.trim())
      else setCreateError("Banco criado mas não foi possível abrir. Recarregue a página.")
    } catch (err) {
      console.error("Failed to create pool:", err)
      setCreateError("Erro de conexão. Verifique sua internet e tente novamente.")
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>Novo Banco de Talentos</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div>
            <label className={textStyles.label}>Nome do banco *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Ex: Backend Sênior SP, Motoristas RJ..."
              className="mt-1 w-full border border-lia-border-default rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
            />
          </div>

          <div>
            <label className={textStyles.label}>Descrição</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Objetivo deste banco de talentos..."
              rows={2}
              className="mt-1 w-full border border-lia-border-default rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
            />
          </div>

          <div>
            <label className={textStyles.label}>Vincular a um Arquétipo</label>
            <p className={`${textStyles.caption} mb-2`}>
              O arquétipo gera automaticamente perguntas de triagem e critérios de avaliação WSI.
            </p>
            {isLoadingArchetypes ? (
              <p className={textStyles.caption}>Carregando arquétipos...</p>
            ) : archetypes.length === 0 ? (
              <p className={textStyles.caption}>Nenhum arquétipo cadastrado. Você pode vincular depois.</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                <label className="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-lia-bg-secondary">
                  <input
                    type="radio"
                    name="archetype"
                    checked={selectedArchetypeId === null}
                    onChange={() => setSelectedArchetypeId(null)}
                    className="rounded-full border-lia-border-default"
                  />
                  <span className={textStyles.body}>Sem arquétipo (configurar depois)</span>
                </label>
                {archetypes.map(a => (
                  <label
                    key={a.id}
                    className="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-lia-bg-secondary"
                  >
                    <input
                      type="radio"
                      name="archetype"
                      checked={selectedArchetypeId === a.id}
                      onChange={() => setSelectedArchetypeId(a.id)}
                      className="rounded-full border-lia-border-default"
                    />
                    <span className={textStyles.body}>{a.name}</span>
                    {a.seniority_level && (
                      <Chip variant="success">{a.seniority_level}</Chip>
                    )}
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>

        {createError && (
          <p className="text-sm text-red-600 px-1 pb-1">{createError}</p>
        )}
        <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={onClose}>
            Cancelar
          </Button>
          <Button
            className={buttonStyles.primary}
            onClick={handleCreate}
            disabled={!name.trim() || isCreating}
          >
            <Plus className="w-4 h-4 mr-1" />
            {isCreating ?"Criando..." :"Criar Banco"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ---------- Move to Job Modal ----------

function MoveToJobModal({ poolId, selectedIds, candidates, onClose, onMoved }: MoveToJobModalProps) {
  const [jobs, setJobs] = useState<Array<{ id: number; title: string }>>([])
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [targetStage, setTargetStage] = useState("interview")
  const [isMoving, setIsMoving] = useState(false)

  // Stages the candidate can be moved to (triagem/sourcing disabled if already screened)
  const hasScreeningData = candidates.some(c => c.screening_data && Object.keys(c.screening_data).length > 0)

  const availableStages = [
    { id:"screening", label:"Triagem", disabled: hasScreeningData },
    { id:"interview", label:"Entrevista", disabled: false },
    { id:"final", label:"Avaliação Final", disabled: false },
  ]

  useEffect(() => {
    fetch("/api/backend-proxy/job-vacancies?status=Ativa&limit=500")
      .then(res => res.json())
      .then(data => {
        const items = data?.items || []
        setJobs(items.map((d: { id: string; title: string }) => ({ id: d.id, title: d.title })))
      })
      .catch((err) => { console.error('[TalentPoolPage] jobs fetch failed', err) })
  }, [])

  const handleMove = async () => {
    if (!selectedJobId) return
    setIsMoving(true)
    try {
      const candidateIds = candidates.map(c => c.candidate.id)
      await fetch(`/api/backend-proxy/talent-pools/${poolId}/move-to-job`, {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({
          job_id: selectedJobId,
          target_stage: targetStage,
          candidate_ids: candidateIds,
        }),
      })
      onMoved(selectedJobId)
    } catch (err) {
      console.error("Move failed:", err)
    } finally {
      setIsMoving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            Mover {candidates.length} candidato{candidates.length > 1 ?"s" :""} para vaga
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Job select */}
          <div>
            <label className={textStyles.label}>Vaga destino</label>
            <select
              value={selectedJobId ||""}
              onChange={e => setSelectedJobId(Number(e.target.value))}
              className="mt-1 w-full border border-lia-border-default rounded-xl px-3 py-2 text-sm"
            >
              <option value="">Selecione uma vaga...</option>
              {jobs.map(j => (
                <option key={j.id} value={j.id}>{j.title}</option>
              ))}
            </select>
          </div>

          {/* Target stage */}
          <div>
            <label className={textStyles.label}>Etapa destino</label>
            <div className="mt-2 space-y-2">
              {availableStages.map(s => (
                <label
                  key={s.id}
                  className={`flex items-center gap-2 ${s.disabled ?"opacity-40 cursor-not-allowed" :"cursor-pointer"}`}
                >
                  <input
                    type="radio"
                    name="target_stage"
                    value={s.id}
                    checked={targetStage === s.id}
                    onChange={() => !s.disabled && setTargetStage(s.id)}
                    disabled={s.disabled}
                    className="rounded-full border-lia-border-default"
                  />
                  <span className={textStyles.body}>{s.label}</span>
                  {s.disabled && (
                    <span className={textStyles.caption}>(já concluída)</span>
                  )}
                </label>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={onClose}>
            Cancelar
          </Button>
          <Button
            className={buttonStyles.primary}
            onClick={handleMove}
            disabled={!selectedJobId || isMoving}
          >
            {isMoving ?"Movendo..." :"Mover candidatos"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
