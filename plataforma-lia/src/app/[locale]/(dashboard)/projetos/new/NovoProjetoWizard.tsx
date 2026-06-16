"use client"

import React, { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft, ArrowRight, Check, Loader2,
  FolderKanban, Briefcase, Megaphone, Search, Bot, User,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog"

// ── Types ──────────────────────────────────────────────────────────────────

interface WizardData {
  // Step 1
  name: string
  campaignType: "sourcing" | "screening" | "end_to_end"
  access: "shared" | "private"
  // Step 2
  jobId: string | null
  talentPoolId: string | null
  // Step 3
  templateKey: string
  stages: Array<{ name: string }>
  // Step 4
  agentId: string | null
  automation_level: "manual" | "semi" | "full"
}

interface JobOption {
  id: string
  title: string
  status: string
  candidates_count?: number
}

interface AgentOption {
  id: string
  name: string
  category: string
  description?: string
  status: string
}

// ── Templates ──────────────────────────────────────────────────────────────

const TEMPLATES = [
  {
    key: "sourcing_focado",
    label: "Sourcing focado",
    stages_count: 4,
    days: 6,
    description: "Banco → Triagem rápida → Convite → Follow-up",
    stages: ["sourcing", "screening", "outreach", "follow_up"],
  },
  {
    key: "multi_canal",
    label: "Multi-canal",
    stages_count: 5,
    days: 8,
    description: "LinkedIn + Email + WhatsApp → Triagem → Entrevista",
    stages: ["sourcing", "screening", "outreach", "interview", "evaluation"],
    popular: true,
  },
  {
    key: "end_to_end_rapido",
    label: "End-to-end rápido",
    stages_count: 5,
    days: 12,
    description: "Sourcing → Triagem → Entrevista → Avaliação → Proposta",
    stages: ["sourcing", "screening", "interview", "evaluation", "offer"],
  },
  {
    key: "triagem_intensiva",
    label: "Triagem intensiva",
    stages_count: 3,
    days: 5,
    description: "WSI + scoring → Decisão rápida → Aprovação gestor",
    stages: ["screening", "evaluation", "offer"],
  },
]

// ── Step indicator ─────────────────────────────────────────────────────────

const STEPS = ["Básico", "Vaga", "Template", "Agente"]

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-0">
      {STEPS.map((label, idx) => {
        const step = idx + 1
        const done = step < current
        const active = step === current
        return (
          <React.Fragment key={label}>
            {idx > 0 && (
              <div
                className={cn(
                  "flex-1 h-px",
                  step <= current ? "bg-lia-btn-primary-bg" : "bg-lia-border-subtle"
                )}
              />
            )}
            <div className="flex flex-col items-center gap-1 shrink-0">
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-colors",
                  done && "bg-lia-btn-primary-bg border-lia-btn-primary-bg text-lia-btn-primary-text",
                  active && "bg-lia-btn-primary-bg border-lia-btn-primary-bg text-lia-btn-primary-text",
                  !done && !active && "bg-lia-bg-primary border-lia-border-subtle text-lia-text-tertiary"
                )}
              >
                {done ? <Check className="w-4 h-4" /> : step}
              </div>
              <span
                className={cn(
                  "text-micro",
                  active ? "text-lia-btn-primary-bg font-medium" : "text-lia-text-tertiary"
                )}
              >
                {label}
              </span>
            </div>
          </React.Fragment>
        )
      })}
    </div>
  )
}

// ── Step 1: Básico ─────────────────────────────────────────────────────────

function Step1Basico({
  data,
  onChange,
}: {
  data: WizardData
  onChange: (patch: Partial<WizardData>) => void
}) {
  const types = [
    { key: "sourcing", label: "Sourcing", icon: Search },
    { key: "screening", label: "Triagem", icon: Briefcase },
    { key: "end_to_end", label: "End-to-end", icon: Megaphone },
  ] as const

  return (
    <div className="space-y-5">
      <div className="space-y-1.5">
        <label className="text-xs font-semibold text-lia-text-primary">Nome da campanha</label>
        <input
          type="text"
          value={data.name}
          onChange={(e) => onChange({ name: e.target.value })}
          placeholder="Ex: SWE Sênior — Engenharia Backend"
          className="w-full px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary text-sm text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
        />
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold text-lia-text-primary">Tipo de campanha</label>
        <div className="grid grid-cols-3 gap-3">
          {types.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => onChange({ campaignType: key })}
              className={cn(
                "flex flex-col items-center gap-2 p-4 rounded-md border text-xs font-medium transition-colors",
                data.campaignType === key
                  ? "border-lia-btn-primary-bg bg-lia-bg-tertiary text-lia-text-primary"
                  : "border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary"
              )}
            >
              <Icon className="w-5 h-5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold text-lia-text-primary">Acesso</label>
        <div className="space-y-2">
          {(["shared", "private"] as const).map((val) => (
            <label key={val} className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="access"
                checked={data.access === val}
                onChange={() => onChange({ access: val })}
                className="mt-0.5 accent-lia-btn-primary-bg"
              />
              <div>
                <p className="text-xs font-semibold text-lia-text-primary">
                  {val === "shared" ? "Compartilhada" : "Privada"}
                </p>
                <p className="text-micro text-lia-text-secondary">
                  {val === "shared"
                    ? "Todos os recrutadores da empresa podem ver e editar"
                    : "Visível apenas para você e convidados"}
                </p>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Step 2: Vaga ───────────────────────────────────────────────────────────

function Step2Vaga({
  data,
  onChange,
}: {
  data: WizardData
  onChange: (patch: Partial<WizardData>) => void
}) {
  const [jobs, setJobs] = useState<JobOption[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetch("/api/backend-proxy/job-vacancies?limit=20&status=publicada,ao_vivo,rascunho,enriquecida")
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return
        const items = (d?.data || d?.jobs || d || []) as Array<{
          id: string; title: string; status: string; candidates_count?: number
        }>
        setJobs(items.filter(Boolean))
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const filtered = jobs.filter(
    (j) =>
      !search ||
      j.title?.toLowerCase().includes(search.toLowerCase())
  )

  const statusLabel: Record<string, string> = {
    publicada: "Publicada",
    ao_vivo: "Ao vivo",
    rascunho: "Rascunho",
    enriquecida: "Enriquecida",
    ats_importada: "Importada",
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <label className="text-xs font-semibold text-lia-text-primary">Vaga vinculada</label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-tertiary pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por título de vaga..."
            className="w-full pl-9 pr-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary text-sm text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
          />
        </div>

        <div className="rounded-md border border-lia-border-subtle overflow-hidden max-h-52 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-6 gap-2 text-lia-text-tertiary">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Carregando vagas...</span>
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-lia-text-tertiary text-center py-6">
              {search ? "Nenhuma vaga encontrada" : "Nenhuma vaga disponível"}
            </p>
          ) : (
            filtered.map((job) => (
              <button
                key={job.id}
                type="button"
                onClick={() => onChange({ jobId: data.jobId === job.id ? null : job.id })}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors border-b border-lia-border-subtle last:border-0",
                  data.jobId === job.id
                    ? "bg-lia-bg-tertiary"
                    : "hover:bg-lia-bg-secondary"
                )}
              >
                <div
                  className={cn(
                    "w-7 h-7 rounded-md flex items-center justify-center shrink-0",
                    data.jobId === job.id
                      ? "bg-lia-bg-primary"
                      : "bg-lia-bg-tertiary"
                  )}
                >
                  <Briefcase
                    className={cn(
                      "w-3.5 h-3.5",
                      data.jobId === job.id ? "text-lia-text-primary" : "text-lia-text-tertiary"
                    )}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      "text-sm font-medium truncate",
                      data.jobId === job.id ? "text-lia-text-primary" : "text-lia-text-primary"
                    )}
                  >
                    {job.title}
                  </p>
                  <p className="text-micro text-lia-text-tertiary">
                    {statusLabel[job.status] ?? job.status}
                    {job.candidates_count != null && ` · ${job.candidates_count} candidatos`}
                  </p>
                </div>
                {data.jobId === job.id && (
                  <Check className="w-4 h-4 text-lia-text-primary shrink-0" />
                )}
              </button>
            ))
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-lia-text-primary">Banco de talentos</label>
          <span className="text-micro text-lia-text-tertiary">Pré-carrega candidatos já conhecidos</span>
        </div>
        <button
          type="button"
          className="w-full flex items-center gap-2 px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary text-sm text-lia-text-tertiary hover:bg-lia-bg-tertiary transition-colors"
          onClick={() => {}}
        >
          <FolderKanban className="w-4 h-4" />
          <span className="flex-1 text-left">Selecionar banco de talentos...</span>
        </button>
      </div>
    </div>
  )
}

// ── Step 3: Template ───────────────────────────────────────────────────────

function Step3Template({
  data,
  onChange,
}: {
  data: WizardData
  onChange: (patch: Partial<WizardData>) => void
}) {
  const modes = ["Gerar com IA", "Do zero", "Templates"] as const
  const [mode, setMode] = useState<(typeof modes)[number]>("Templates")

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-2">
        {modes.map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={cn(
              "rounded-md border px-3 py-2 text-xs font-medium text-center transition-colors",
              mode === m
                ? "border-lia-btn-primary-bg bg-lia-bg-tertiary text-lia-text-primary"
                : "border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary"
            )}
          >
            {m}
          </button>
        ))}
      </div>

      {mode === "Templates" && (
        <div>
          <p className="text-sm text-lia-text-secondary mb-3">Selecione um template de sequência</p>
          <div className="grid grid-cols-2 gap-3">
            {TEMPLATES.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() =>
                  onChange({
                    templateKey: t.key,
                    stages: t.stages.map((s) => ({ name: s })),
                  })
                }
                className={cn(
                  "relative p-4 rounded-md border text-left transition-colors",
                  data.templateKey === t.key
                    ? "border-lia-btn-primary-bg bg-lia-bg-tertiary"
                    : "border-lia-border-subtle bg-lia-bg-secondary hover:bg-lia-bg-tertiary"
                )}
              >
                {t.popular && (
                  <span className="absolute top-2 right-2 text-micro font-semibold px-1.5 py-0.5 rounded-full bg-lia-btn-primary-bg text-lia-btn-primary-text">
                    Popular
                  </span>
                )}
                <p className="text-sm font-semibold text-lia-text-primary mb-2">{t.label}</p>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-micro px-1.5 py-0.5 rounded-full bg-lia-bg-paper text-lia-text-secondary">
                    {t.stages_count} etapas
                  </span>
                  <span className="text-micro px-1.5 py-0.5 rounded-full bg-lia-bg-paper text-lia-text-secondary">
                    {t.days} dias
                  </span>
                </div>
                <p className="text-micro text-lia-text-secondary leading-snug">{t.description}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {mode === "Do zero" && (
        <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
          <FolderKanban className="w-10 h-10 text-lia-text-tertiary" />
          <p className="text-sm text-lia-text-secondary">
            Você configurará as etapas manualmente após criar o projeto.
          </p>
          <button
            type="button"
            onClick={() => onChange({ templateKey: "custom", stages: [] })}
            className={cn(
              "px-4 py-2 rounded-md border text-xs font-medium transition-colors",
              data.templateKey === "custom"
                ? "border-lia-btn-primary-bg bg-lia-bg-tertiary text-lia-text-primary"
                : "border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary"
            )}
          >
            {data.templateKey === "custom" ? "✓ Selecionado" : "Continuar sem template"}
          </button>
        </div>
      )}

      {mode === "Gerar com IA" && (
        <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
          <Bot className="w-10 h-10 text-lia-text-tertiary" />
          <p className="text-sm text-lia-text-secondary">
            A IA gerará um pipeline otimizado com base na vaga selecionada.
          </p>
          <button
            type="button"
            onClick={() => onChange({ templateKey: "ai_generated", stages: [] })}
            className={cn(
              "px-4 py-2 rounded-md border text-xs font-medium transition-colors",
              data.templateKey === "ai_generated"
                ? "border-lia-btn-primary-bg bg-lia-bg-tertiary text-lia-text-primary"
                : "border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-bg-tertiary"
            )}
          >
            {data.templateKey === "ai_generated" ? "✓ Selecionado" : "Gerar pipeline com IA"}
          </button>
        </div>
      )}
    </div>
  )
}

// ── Step 4: Agente ─────────────────────────────────────────────────────────

function Step4Agente({
  data,
  onChange,
}: {
  data: WizardData
  onChange: (patch: Partial<WizardData>) => void
}) {
  const [agents, setAgents] = useState<AgentOption[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetch("/api/backend-proxy/custom-agents?status=active&limit=10")
      .then((r) => r.json())
      .then((d) => {
        if (!cancelled) {
          const items = (d?.agents || d?.data || d || []) as AgentOption[]
          setAgents(items.filter((a) => a.status === "active" || a.status === "paused" || !a.status))
        }
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const categoryLabel: Record<string, string> = {
    sourcing: "Sourcing",
    screening: "Triagem",
    communication: "Comunicação",
    interview: "Entrevista",
  }

  const selectAgent = (id: string | null) => {
    onChange({
      agentId: id,
      automation_level: id === null ? "manual" : "full",
    })
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-lia-text-secondary">Selecione o agente responsável por esta campanha</p>

      {loading ? (
        <div className="flex items-center justify-center py-6 gap-2 text-lia-text-tertiary">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">Carregando agentes...</span>
        </div>
      ) : (
        <div className="space-y-2">
          {agents.map((agent) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => selectAgent(agent.id)}
              className={cn(
                "w-full flex items-center gap-3 p-3 rounded-md border text-left transition-colors",
                data.agentId === agent.id
                  ? "border-lia-btn-primary-bg bg-lia-bg-tertiary"
                  : "border-lia-border-subtle hover:bg-lia-bg-tertiary bg-lia-bg-secondary"
              )}
            >
              <div
                className={cn(
                  "w-9 h-9 rounded-md flex items-center justify-center shrink-0",
                  data.agentId === agent.id ? "bg-lia-bg-primary" : "bg-lia-bg-secondary"
                )}
              >
                <Bot
                  className={cn(
                    "w-4 h-4",
                    data.agentId === agent.id ? "text-lia-text-primary" : "text-lia-text-secondary"
                  )}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "text-sm font-medium",
                      data.agentId === agent.id ? "text-lia-text-primary" : "text-lia-text-primary"
                    )}
                  >
                    {agent.name}
                  </span>
                  {agent.category && (
                    <span className="text-micro px-1.5 py-0.5 rounded-full bg-lia-bg-secondary text-lia-text-tertiary">
                      {categoryLabel[agent.category] ?? agent.category}
                    </span>
                  )}
                </div>
                {agent.description && (
                  <p className="text-micro text-lia-text-secondary mt-0.5 truncate">{agent.description}</p>
                )}
              </div>
              {data.agentId === agent.id && (
                <Check className="w-4 h-4 text-lia-text-primary shrink-0" />
              )}
            </button>
          ))}

          <button
            type="button"
            onClick={() => selectAgent(null)}
            className={cn(
              "w-full flex items-center gap-3 p-3 rounded-md border text-left transition-colors",
              data.agentId === null
                ? "border-lia-btn-primary-bg bg-lia-bg-tertiary"
                : "border-dashed border-lia-border-subtle hover:bg-lia-bg-tertiary bg-lia-bg-secondary"
            )}
          >
            <div className="w-9 h-9 rounded-md bg-lia-bg-tertiary flex items-center justify-center shrink-0">
              <User className="w-4 h-4 text-lia-text-tertiary" />
            </div>
            <span
              className={cn(
                "text-sm",
                data.agentId === null ? "text-lia-text-primary font-medium" : "text-lia-text-secondary"
              )}
            >
              Sem agente — gerenciar manualmente
            </span>
            {data.agentId === null && (
              <Check className="w-4 h-4 text-lia-text-primary shrink-0 ml-auto" />
            )}
          </button>
        </div>
      )}
    </div>
  )
}

// ── Main wizard ────────────────────────────────────────────────────────────

const INITIAL: WizardData = {
  name: "",
  campaignType: "end_to_end",
  access: "shared",
  jobId: null,
  talentPoolId: null,
  templateKey: "multi_canal",
  stages: TEMPLATES[1].stages.map((s) => ({ name: s })),
  agentId: null,
  automation_level: "semi",
}

function canAdvance(step: number, data: WizardData): boolean {
  if (step === 1) return data.name.trim().length >= 2
  if (step === 2) return true
  if (step === 3) return data.templateKey.length > 0
  return true
}

export function NovoProjetoWizard({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [data, setData] = useState<WizardData>(INITIAL)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const patch = useCallback((p: Partial<WizardData>) => {
    setData((prev) => ({ ...prev, ...p }))
  }, [])

  const handleNext = () => {
    if (step < 4) setStep((s) => s + 1)
  }

  const handleBack = () => {
    if (step > 1) setStep((s) => s - 1)
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const payload = {
        name: data.name.trim(),
        description: null,
        job_id: data.jobId,
        talent_pool_id: data.talentPoolId,
        automation_level: data.automation_level,
        stages: data.stages,
      }
      const res = await fetch("/api/backend-proxy/recruitment-campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.detail ?? "Erro ao criar projeto")
      }
      const json = await res.json()
      const created = ("ok" in json ? json.data : json)
      onClose()
      router.push(`/pt/projetos/${created.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="max-w-2xl bg-lia-bg-primary border-lia-border-subtle max-h-[90vh] overflow-y-auto"
        data-testid="novo-projeto-wizard"
      >
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-lia-text-primary flex items-center gap-2">
            <FolderKanban className="w-4 h-4 text-graphite" />
            Novo projeto de recrutamento
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-muted">
            Etapa {step} de 4 — {STEPS[step - 1]}
          </DialogDescription>
        </DialogHeader>

        {/* Progress bar */}
        <div className="flex items-center gap-1 pb-1">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={cn(
                "h-1 flex-1 rounded-full transition-colors duration-200",
                s <= step ? "bg-graphite" : "bg-lia-bg-tertiary",
              )}
            />
          ))}
        </div>

        <div className="py-2 max-h-[60vh] overflow-y-auto">
          {step === 1 && <Step1Basico data={data} onChange={patch} />}
          {step === 2 && <Step2Vaga data={data} onChange={patch} />}
          {step === 3 && <Step3Template data={data} onChange={patch} />}
          {step === 4 && <Step4Agente data={data} onChange={patch} />}
          {error && (
            <p className="mt-3 text-sm text-lia-text-error">{error}</p>
          )}
        </div>

        <DialogFooter className="flex items-center justify-between gap-2">
          <div>
            {step > 1 && (
              <Button variant="ghost" onClick={handleBack} disabled={submitting}>
                Voltar
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={onClose} disabled={submitting}>
              Cancelar
            </Button>
            {step < 4 ? (
              <Button
                onClick={handleNext}
                disabled={!canAdvance(step, data)}
                className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
              >
                Próximo
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitting || !canAdvance(4, data)}
                className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
              >
                {submitting && <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />}
                Criar projeto
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
