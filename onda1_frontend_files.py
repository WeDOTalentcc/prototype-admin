#!/usr/bin/env python3
"""
Onda 1: Agent Studio Frontend — Foundation + Template Gallery + My Agents
Creates all files respecting existing architecture:
- LIA Chat stays on the RIGHT (existing LiaSplitPanel/LiaChatPanel)
- Agent Studio content on the LEFT (main area)
- Design tokens from src/lib/design-tokens.ts
- shadcn/ui components from src/components/ui/
- Zustand pattern from stores/wizard-store.ts
- Proxy route pattern from api/backend-proxy/custom-agents/route.ts
"""
import os

BASE = "/home/runner/workspace/plataforma-lia/src"


def write(rel_path, content):
    full = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {rel_path}")


# ============================================================
# 1. TYPES
# ============================================================
print("\n=== 1. Types ===")
write("components/pages-agent-studio/custom-agents/types.ts", '''/**
 * Agent Studio — Shared TypeScript types
 * Mirrors backend schemas (app/schemas/custom_agent.py + agent_deployment.py)
 */

export type AgentCategory = "screening" | "sourcing" | "communication" | "analytics" | "job_management" | "automation"

export type ContextLevel = "full" | "standard" | "minimal"

export type AgentStatus = "draft" | "active" | "paused" | "archived"

export type DeploymentTargetType = "job" | "talent_pool" | "pipeline_stage" | "candidate_list"

export type TriggerMode = "manual" | "on_new_candidate" | "on_stage_change" | "scheduled"

export interface AgentTemplate {
  id: string
  name: string
  description: string
  category: AgentCategory
  domain: string
  icon: string
  system_prompt: string
  allowed_tools: string[]
  context_level: ContextLevel
  max_steps: number
  temperature: number
  enable_memory: boolean
  excluded_tools: string[]
  tags: string[]
}

export interface CustomAgent {
  id: string
  company_id: string
  name: string
  role: string
  description: string | null
  system_prompt: string
  allowed_tools: string[]
  domain: string
  icon: string
  status: AgentStatus
  config: Record<string, unknown>
  max_steps: number
  temperature: number
  model_override: string | null
  enable_memory: boolean
  context_level: ContextLevel
  excluded_tools: string[]
  total_executions: number
  avg_confidence: number
  last_executed_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface AgentDeployment {
  id: string
  agent_id: string
  company_id: string
  target_type: DeploymentTargetType
  target_id: string
  target_name: string | null
  trigger_mode: TriggerMode
  schedule_cron: string | null
  is_active: boolean
  config_overrides: Record<string, unknown>
  execution_count: number
  candidates_processed: number
  last_execution_at: string | null
  created_by: string
  created_at: string | null
}

export interface CreateDeploymentRequest {
  target_type: DeploymentTargetType
  target_id: string
  target_name?: string
  trigger_mode?: TriggerMode
  schedule_cron?: string
  config_overrides?: Record<string, unknown>
}

/** Human-readable labels for category display */
export const CATEGORY_LABELS: Record<AgentCategory, string> = {
  screening: "Triagem",
  sourcing: "Sourcing",
  communication: "Comunicacao",
  analytics: "Analise",
  job_management: "Vagas",
  automation: "Automacao",
}

/** Human-readable labels for tools */
export const TOOL_LABELS: Record<string, string> = {
  search_candidates: "Buscar candidatos",
  list_jobs: "Listar vagas",
  get_job_details: "Ver detalhes da vaga",
  get_candidate_details: "Ver detalhes do candidato",
  get_pipeline_summary: "Resumo do pipeline",
  search_talent_pool: "Buscar no banco de talentos",
  get_analytics_summary: "Resumo de analytics",
  get_company_culture: "Cultura da empresa",
  get_evaluation_criteria: "Criterios de avaliacao",
  summarize_context: "Resumir contexto",
  clarify_request: "Pedir esclarecimento",
  move_candidate: "Mover candidato",
  send_email: "Enviar email",
  update_candidate_field: "Atualizar candidato",
  schedule_interview: "Agendar entrevista",
  create_note: "Criar anotacao",
}

export const TRIGGER_LABELS: Record<TriggerMode, string> = {
  manual: "Manual",
  on_new_candidate: "A cada novo candidato",
  on_stage_change: "Ao mudar de etapa",
  scheduled: "Agendado",
}

export const TARGET_LABELS: Record<DeploymentTargetType, string> = {
  job: "Vaga",
  talent_pool: "Banco de Talentos",
  pipeline_stage: "Etapa do Pipeline",
  candidate_list: "Lista de Candidatos",
}
''')


# ============================================================
# 2. ZUSTAND STORE
# ============================================================
print("\n=== 2. Zustand Store ===")
write("stores/agent-studio-store.ts", '''"use client"

import { create } from "zustand"
import { devtools } from "zustand/middleware"
import type { AgentTemplate, CustomAgent, AgentCategory } from "@/components/pages-agent-studio/custom-agents/types"

type CreationMode = "idle" | "template" | "manual"

interface AgentStudioState {
  // Creation flow
  creationMode: CreationMode
  selectedTemplate: AgentTemplate | null
  draftAgent: Partial<CustomAgent>

  // Gallery filters
  activeCategory: AgentCategory | "all"

  // Actions
  setCreationMode: (mode: CreationMode) => void
  selectTemplate: (template: AgentTemplate) => void
  updateDraft: (partial: Partial<CustomAgent>) => void
  setActiveCategory: (category: AgentCategory | "all") => void
  reset: () => void
}

export const useAgentStudioStore = create<AgentStudioState>()(
  devtools(
    (set) => ({
      creationMode: "idle",
      selectedTemplate: null,
      draftAgent: {},
      activeCategory: "all",

      setCreationMode: (mode) => set({ creationMode: mode }),

      selectTemplate: (template) =>
        set({
          selectedTemplate: template,
          creationMode: "template",
          draftAgent: {
            name: template.name,
            role: template.description,
            description: template.description,
            system_prompt: template.system_prompt,
            allowed_tools: template.allowed_tools,
            domain: template.domain,
            icon: template.icon,
            context_level: template.context_level,
            max_steps: template.max_steps,
            temperature: template.temperature,
            enable_memory: template.enable_memory,
            excluded_tools: template.excluded_tools,
          },
        }),

      updateDraft: (partial) =>
        set((state) => ({ draftAgent: { ...state.draftAgent, ...partial } })),

      setActiveCategory: (category) => set({ activeCategory: category }),

      reset: () =>
        set({
          creationMode: "idle",
          selectedTemplate: null,
          draftAgent: {},
        }),
    }),
    { name: "agent-studio" }
  )
)
''')


# ============================================================
# 3. SWR HOOKS
# ============================================================
print("\n=== 3. SWR Hooks ===")
write("hooks/agents/use-custom-agents.ts", '''"use client"

import useSWR from "swr"
import type { CustomAgent } from "@/components/pages-agent-studio/custom-agents/types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`)
  return res.json()
}

export function useCustomAgents() {
  const { data, error, isLoading, mutate } = useSWR<{ agents: CustomAgent[]; total: number }>(
    "/api/backend-proxy/custom-agents",
    fetcher,
    { revalidateOnFocus: false, dedupingInterval: 5000 }
  )
  return {
    agents: data?.agents ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}

export function useAgentDeployments(agentId: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    agentId ? `/api/backend-proxy/custom-agents/${agentId}/deployments` : null,
    fetcher,
    { revalidateOnFocus: false }
  )
  return {
    deployments: data?.deployments ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}
''')

write("hooks/agents/index.ts", '''export { useCustomAgents, useAgentDeployments } from "./use-custom-agents"
''')


# ============================================================
# 4. TEMPLATE DATA (15 templates)
# ============================================================
print("\n=== 4. Template Data ===")
write("lib/agent-templates-data.ts", '''/**
 * Agent Templates — Pre-configured agent recipes for common recruiting scenarios.
 * Each template pre-fills all fields so the recruiter can activate in 1 click.
 * Migrates to backend /agent-templates API in a future sprint.
 */
import type { AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"

export const AGENT_TEMPLATES: AgentTemplate[] = [
  {
    id: "tpl-triagem-tech",
    name: "Triagem Tech",
    description: "Filtra candidatos de tecnologia por stack, experiencia e senioridade. Avalia fit tecnico automaticamente.",
    category: "screening",
    domain: "screening",
    icon: "Code",
    system_prompt: "Voce e um agente de triagem tecnica. Analise o CV do candidato focando em: stack tecnologico, anos de experiencia, projetos relevantes e senioridade. Classifique de 1-10 com justificativa.",
    allowed_tools: ["search_candidates", "get_candidate_details", "get_evaluation_criteria", "create_note"],
    context_level: "standard",
    max_steps: 8,
    temperature: 0.3,
    enable_memory: true,
    excluded_tools: [],
    tags: ["popular", "tech", "triagem"],
  },
  {
    id: "tpl-triagem-volume",
    name: "Triagem Volume",
    description: "Processa alto volume de candidaturas rapidamente. Ideal para vagas operacionais, varejo e atendimento.",
    category: "screening",
    domain: "screening",
    icon: "Users",
    system_prompt: "Voce e um agente de triagem rapida para vagas de alto volume. Avalie cada candidato em menos de 30 segundos focando nos requisitos minimos: disponibilidade, localizacao e experiencia basica.",
    allowed_tools: ["search_candidates", "get_candidate_details", "move_candidate"],
    context_level: "minimal",
    max_steps: 5,
    temperature: 0.2,
    enable_memory: false,
    excluded_tools: [],
    tags: ["volume", "rapido", "operacional"],
  },
  {
    id: "tpl-screening-cultural",
    name: "Screening Cultural",
    description: "Avalia fit cultural do candidato com base nos valores e cultura da empresa.",
    category: "screening",
    domain: "screening",
    icon: "Heart",
    system_prompt: "Voce e um agente de screening cultural. Use os valores da empresa e o perfil cultural para avaliar compatibilidade. Foque em soft skills, motivacao e alinhamento de valores. Nunca pergunte sobre idade, genero, religiao ou estado civil.",
    allowed_tools: ["get_candidate_details", "get_company_culture", "get_evaluation_criteria", "create_note"],
    context_level: "full",
    max_steps: 8,
    temperature: 0.5,
    enable_memory: true,
    excluded_tools: [],
    tags: ["cultura", "soft-skills", "valores"],
  },
  {
    id: "tpl-sourcing-passivo",
    name: "Sourcing Passivo",
    description: "Busca candidatos que nao se candidataram ativamente. Mapeia talentos em bancos de dados e pools.",
    category: "sourcing",
    domain: "sourcing",
    icon: "Search",
    system_prompt: "Voce e um agente de sourcing passivo. Busque candidatos que correspondam ao perfil da vaga em bancos de talentos e listas. Priorize candidatos com experiencia relevante que nao se candidataram recentemente.",
    allowed_tools: ["search_candidates", "search_talent_pool", "get_candidate_details", "get_job_details"],
    context_level: "standard",
    max_steps: 10,
    temperature: 0.4,
    enable_memory: true,
    excluded_tools: [],
    tags: ["sourcing", "passivo", "headhunting"],
  },
  {
    id: "tpl-sourcing-diversidade",
    name: "Sourcing Diversidade",
    description: "Busca com guardrails de diversidade e inclusao. Garante representatividade no funil.",
    category: "sourcing",
    domain: "sourcing",
    icon: "Globe",
    system_prompt: "Voce e um agente de sourcing com foco em diversidade. Busque candidatos garantindo representatividade no funil. NUNCA filtre por genero, raca, idade, religiao ou orientacao. Foque em competencias e potencial.",
    allowed_tools: ["search_candidates", "search_talent_pool", "get_candidate_details", "get_analytics_summary"],
    context_level: "full",
    max_steps: 10,
    temperature: 0.5,
    enable_memory: true,
    excluded_tools: [],
    tags: ["diversidade", "inclusao", "dei"],
  },
  {
    id: "tpl-agendamento",
    name: "Agendamento Entrevista",
    description: "Agenda entrevistas automaticamente coordenando disponibilidade do candidato e entrevistador.",
    category: "communication",
    domain: "communication",
    icon: "Calendar",
    system_prompt: "Voce e um agente de agendamento. Coordene a agenda do candidato e do entrevistador para encontrar o melhor horario. Seja cordial e eficiente. Ofereca 2-3 opcoes de horario.",
    allowed_tools: ["get_candidate_details", "schedule_interview", "send_email"],
    context_level: "minimal",
    max_steps: 6,
    temperature: 0.3,
    enable_memory: false,
    excluded_tools: [],
    tags: ["agenda", "entrevista", "scheduling"],
  },
  {
    id: "tpl-followup",
    name: "Follow-up Candidato",
    description: "Envia acompanhamento automatico apos entrevistas. Mantem o candidato engajado no processo.",
    category: "communication",
    domain: "communication",
    icon: "MessageCircle",
    system_prompt: "Voce e um agente de follow-up. Envie mensagens de acompanhamento personalizadas apos entrevistas. Seja profissional, empatetico e transparente sobre proximos passos.",
    allowed_tools: ["get_candidate_details", "send_email", "get_pipeline_summary"],
    context_level: "standard",
    max_steps: 5,
    temperature: 0.6,
    enable_memory: true,
    excluded_tools: [],
    tags: ["follow-up", "engajamento", "comunicacao"],
  },
  {
    id: "tpl-analise-pipeline",
    name: "Analise Pipeline",
    description: "Analisa metricas e gargalos do funil de recrutamento. Identifica onde candidatos estao travando.",
    category: "analytics",
    domain: "analytics",
    icon: "BarChart3",
    system_prompt: "Voce e um analista de pipeline. Identifique gargalos no funil, tempo medio por etapa, taxas de conversao e onde candidatos estao abandonando. Sugira acoes concretas para melhorar.",
    allowed_tools: ["get_pipeline_summary", "get_analytics_summary", "list_jobs"],
    context_level: "standard",
    max_steps: 8,
    temperature: 0.3,
    enable_memory: false,
    excluded_tools: [],
    tags: ["pipeline", "metricas", "gargalos"],
  },
  {
    id: "tpl-comparacao",
    name: "Comparacao Candidatos",
    description: "Compara finalistas lado a lado com ranking objetivo baseado nos criterios da vaga.",
    category: "analytics",
    domain: "analytics",
    icon: "GitCompare",
    system_prompt: "Voce e um analista de candidatos. Compare os finalistas lado a lado usando os criterios da vaga. Crie um ranking objetivo com pontuacao e justificativa para cada dimensao avaliada.",
    allowed_tools: ["get_candidate_details", "get_evaluation_criteria", "get_job_details", "create_note"],
    context_level: "full",
    max_steps: 10,
    temperature: 0.3,
    enable_memory: true,
    excluded_tools: [],
    tags: ["comparacao", "ranking", "finalistas"],
  },
  {
    id: "tpl-assistente-vaga",
    name: "Assistente de Vaga",
    description: "Ajuda a criar e otimizar descricoes de vagas. Sugere melhorias baseadas em boas praticas.",
    category: "job_management",
    domain: "job_management",
    icon: "FileEdit",
    system_prompt: "Voce e um especialista em job descriptions. Ajude o recrutador a criar descricoes claras, inclusivas e atrativas. Sugira skills relevantes, faixas salariais competitivas e beneficios.",
    allowed_tools: ["get_job_details", "list_jobs", "get_analytics_summary"],
    context_level: "standard",
    max_steps: 8,
    temperature: 0.7,
    enable_memory: true,
    excluded_tools: [],
    tags: ["vaga", "job-description", "otimizacao"],
  },
  {
    id: "tpl-onboarding-prep",
    name: "Onboarding Prep",
    description: "Prepara o processo de onboarding apos a contratacao. Organiza documentos e tarefas iniciais.",
    category: "automation",
    domain: "automation",
    icon: "Rocket",
    system_prompt: "Voce e um agente de onboarding. Prepare a integracao do novo colaborador: liste documentos necessarios, tarefas da primeira semana, pessoas para conhecer e recursos para acessar.",
    allowed_tools: ["get_candidate_details", "create_note", "send_email"],
    context_level: "standard",
    max_steps: 8,
    temperature: 0.5,
    enable_memory: true,
    excluded_tools: [],
    tags: ["onboarding", "integracao", "novo-colaborador"],
  },
  {
    id: "tpl-salary-benchmark",
    name: "Salary Benchmark",
    description: "Pesquisa benchmark salarial para a vaga com base em dados de mercado.",
    category: "analytics",
    domain: "analytics",
    icon: "DollarSign",
    system_prompt: "Voce e um analista de remuneracao. Pesquise e apresente benchmarks salariais para a vaga considerando senioridade, localizacao, setor e porte da empresa. Apresente faixas (P25, P50, P75).",
    allowed_tools: ["get_job_details", "get_analytics_summary"],
    context_level: "minimal",
    max_steps: 6,
    temperature: 0.3,
    enable_memory: false,
    excluded_tools: [],
    tags: ["salario", "benchmark", "remuneracao"],
  },
  {
    id: "tpl-feedback-collector",
    name: "Feedback Collector",
    description: "Coleta e organiza feedback de entrevistadores de forma estruturada.",
    category: "communication",
    domain: "communication",
    icon: "ClipboardCheck",
    system_prompt: "Voce e um agente de coleta de feedback. Solicite feedback estruturado dos entrevistadores sobre cada candidato: pontos fortes, areas de melhoria, recomendacao (sim/nao/talvez) e justificativa.",
    allowed_tools: ["get_candidate_details", "send_email", "create_note"],
    context_level: "standard",
    max_steps: 6,
    temperature: 0.4,
    enable_memory: true,
    excluded_tools: [],
    tags: ["feedback", "entrevistadores", "avaliacao"],
  },
  {
    id: "tpl-talent-pool-curator",
    name: "Talent Pool Curator",
    description: "Organiza e rankeia candidatos no banco de talentos. Mantem o pool atualizado e relevante.",
    category: "sourcing",
    domain: "sourcing",
    icon: "Database",
    system_prompt: "Voce e um curador de banco de talentos. Analise os candidatos no pool, remova perfis desatualizados, categorize por area de atuacao e ranqueie por relevancia para vagas abertas.",
    allowed_tools: ["search_talent_pool", "get_candidate_details", "get_job_details", "create_note"],
    context_level: "standard",
    max_steps: 10,
    temperature: 0.4,
    enable_memory: true,
    excluded_tools: [],
    tags: ["talent-pool", "curadoria", "organizacao"],
  },
  {
    id: "tpl-compliance-check",
    name: "Compliance Check",
    description: "Valida requisitos legais e de compliance do processo seletivo.",
    category: "screening",
    domain: "screening",
    icon: "ShieldCheck",
    system_prompt: "Voce e um agente de compliance. Verifique se o processo seletivo atende requisitos legais: LGPD, igualdade de oportunidades, documentacao necessaria e prazos regulatorios. Sinalize riscos.",
    allowed_tools: ["get_job_details", "get_candidate_details", "get_pipeline_summary", "create_note"],
    context_level: "full",
    max_steps: 8,
    temperature: 0.2,
    enable_memory: false,
    excluded_tools: [],
    tags: ["compliance", "lgpd", "legal"],
  },
]

export const TEMPLATE_CATEGORIES = [
  { id: "all" as const, label: "Todos", icon: "LayoutGrid" },
  { id: "screening" as const, label: "Triagem", icon: "Filter" },
  { id: "sourcing" as const, label: "Sourcing", icon: "Search" },
  { id: "communication" as const, label: "Comunicacao", icon: "MessageCircle" },
  { id: "analytics" as const, label: "Analise", icon: "BarChart3" },
  { id: "job_management" as const, label: "Vagas", icon: "Briefcase" },
  { id: "automation" as const, label: "Automacao", icon: "Zap" },
]
''')


# ============================================================
# 5. TEMPLATE CARD
# ============================================================
print("\n=== 5. TemplateCard ===")
write("components/pages-agent-studio/custom-agents/TemplateCard.tsx", '''"use client"

import React from "react"
import * as Icons from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
import type { AgentTemplate } from "./types"
import { CATEGORY_LABELS } from "./types"

interface TemplateCardProps {
  template: AgentTemplate
  onSelect: (template: AgentTemplate) => void
}

export function TemplateCard({ template, onSelect }: TemplateCardProps) {
  const IconComponent = (Icons as Record<string, React.ComponentType<{ className?: string }>>)[template.icon] || Icons.Bot

  return (
    <button
      type="button"
      onClick={() => onSelect(template)}
      className={cn(
        cardStyles.interactive,
        "p-4 text-left w-full flex flex-col gap-2 group"
      )}
    >
      <div className="flex items-start justify-between">
        <div className="w-9 h-9 rounded-md bg-wedo-cyan/10 flex items-center justify-center shrink-0">
          <IconComponent className="w-4 h-4 text-wedo-cyan-dark" />
        </div>
        {template.tags.includes("popular") && (
          <span className={badgeStyles.cyan}>Popular</span>
        )}
      </div>

      <div>
        <h4 className={cn(textStyles.subtitle, "text-sm font-semibold leading-tight")}>
          {template.name}
        </h4>
        <p className={cn(textStyles.caption, "mt-1 text-xs leading-relaxed line-clamp-2")}>
          {template.description}
        </p>
      </div>

      <div className="flex items-center gap-1.5 mt-auto pt-1">
        <span className={cn(badgeStyles.default, "text-[10px]")}>
          {CATEGORY_LABELS[template.category]}
        </span>
        <span className={cn(badgeStyles.default, "text-[10px]")}>
          {template.allowed_tools.length} ferramentas
        </span>
      </div>
    </button>
  )
}
''')


# ============================================================
# 6. TEMPLATE GALLERY
# ============================================================
print("\n=== 6. TemplateGallery ===")
write("components/pages-agent-studio/custom-agents/TemplateGallery.tsx", '''"use client"

import React from "react"
import * as Icons from "lucide-react"
import { cn } from "@/lib/utils"
import { buttonStyles, textStyles } from "@/lib/design-tokens"
import { AGENT_TEMPLATES, TEMPLATE_CATEGORIES } from "@/lib/agent-templates-data"
import { useAgentStudioStore } from "@/stores/agent-studio-store"
import { TemplateCard } from "./TemplateCard"
import type { AgentTemplate, AgentCategory } from "./types"

interface TemplateGalleryProps {
  onTemplateSelect: (template: AgentTemplate) => void
  onCreateManual: () => void
}

export function TemplateGallery({ onTemplateSelect, onCreateManual }: TemplateGalleryProps) {
  const { activeCategory, setActiveCategory } = useAgentStudioStore()

  const filtered = activeCategory === "all"
    ? AGENT_TEMPLATES
    : AGENT_TEMPLATES.filter((t) => t.category === activeCategory)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className={cn(textStyles.title, "text-lg")}>Comece com um template</h3>
          <p className={cn(textStyles.caption, "mt-0.5")}>
            Escolha um modelo pronto ou descreva para a LIA o que voce precisa no chat
          </p>
        </div>
        <button
          type="button"
          onClick={onCreateManual}
          className={cn(buttonStyles.outline, "text-xs px-3 py-1.5")}
        >
          <Icons.Plus className="w-3.5 h-3.5 mr-1.5" />
          Criar do zero
        </button>
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-1.5">
        {TEMPLATE_CATEGORIES.map((cat) => {
          const CatIcon = (Icons as Record<string, React.ComponentType<{ className?: string }>>)[cat.icon] || Icons.LayoutGrid
          const isActive = activeCategory === cat.id
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => setActiveCategory(cat.id as AgentCategory | "all")}
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
                isActive
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary"
                  : "bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-secondary dark:text-lia-text-secondary"
              )}
            >
              <CatIcon className="w-3.5 h-3.5" />
              {cat.label}
            </button>
          )
        })}
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onSelect={onTemplateSelect}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-10">
          <Icons.SearchX className="w-8 h-8 mx-auto text-lia-text-disabled mb-2" />
          <p className={textStyles.caption}>Nenhum template nesta categoria</p>
        </div>
      )}
    </div>
  )
}
''')


# ============================================================
# 7. AGENT CARD (My Agents list item)
# ============================================================
print("\n=== 7. AgentCard ===")
write("components/pages-agent-studio/custom-agents/AgentCard.tsx", '''"use client"

import React from "react"
import { Bot, Play, Pause, MoreVertical, Link2, TestTube2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import type { CustomAgent } from "./types"
import { CATEGORY_LABELS } from "./types"

const STATUS_STYLES: Record<string, { label: string; badge: string }> = {
  draft: { label: "Rascunho", badge: badgeStyles.default },
  active: { label: "Ativo", badge: badgeStyles.success },
  paused: { label: "Pausado", badge: badgeStyles.warning },
  archived: { label: "Arquivado", badge: badgeStyles.error },
}

interface AgentCardProps {
  agent: CustomAgent
  onTest: (agent: CustomAgent) => void
  onDeploy: (agent: CustomAgent) => void
  onToggleStatus: (agent: CustomAgent) => void
}

export function AgentCard({ agent, onTest, onDeploy, onToggleStatus }: AgentCardProps) {
  const statusStyle = STATUS_STYLES[agent.status] || STATUS_STYLES.draft
  const category = (agent.domain || "general") as keyof typeof CATEGORY_LABELS
  const categoryLabel = CATEGORY_LABELS[category] || agent.domain

  return (
    <div className={cn(cardStyles.default, "p-4 flex flex-col gap-3")}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-wedo-cyan/10 flex items-center justify-center">
            <Bot className="w-4 h-4 text-wedo-cyan-dark" />
          </div>
          <div>
            <h4 className={cn(textStyles.subtitle, "text-sm font-semibold leading-tight")}>
              {agent.name}
            </h4>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn(badgeStyles.default, "text-[10px]")}>{categoryLabel}</span>
              <span className={cn(statusStyle.badge, "text-[10px]")}>{statusStyle.label}</span>
            </div>
          </div>
        </div>
        <BetaBadge size="sm" />
      </div>

      {/* Description */}
      {agent.description && (
        <p className={cn(textStyles.caption, "text-xs line-clamp-2")}>{agent.description}</p>
      )}

      {/* Metrics */}
      <div className="flex items-center gap-4 text-xs">
        <div>
          <span className="font-bold text-lia-text-primary font-inter">{agent.total_executions}</span>
          <span className="text-lia-text-disabled ml-1">execucoes</span>
        </div>
        {agent.avg_confidence > 0 && (
          <div>
            <span className="font-bold text-lia-text-primary font-inter">{(agent.avg_confidence * 100).toFixed(0)}%</span>
            <span className="text-lia-text-disabled ml-1">confianca</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t border-lia-border-subtle">
        <button
          type="button"
          onClick={() => onTest(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
        >
          <TestTube2 className="w-3.5 h-3.5" /> Testar
        </button>
        <button
          type="button"
          onClick={() => onDeploy(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-wedo-cyan-dark hover:bg-wedo-cyan/10 transition-colors"
        >
          <Link2 className="w-3.5 h-3.5" /> Vincular
        </button>
        <button
          type="button"
          onClick={() => onToggleStatus(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors ml-auto"
        >
          {agent.status === "active" ? (
            <><Pause className="w-3.5 h-3.5" /> Pausar</>
          ) : (
            <><Play className="w-3.5 h-3.5" /> Ativar</>
          )}
        </button>
      </div>
    </div>
  )
}
''')


# ============================================================
# 8. DEPLOY DIALOG
# ============================================================
print("\n=== 8. DeployDialog ===")
write("components/pages-agent-studio/custom-agents/DeployDialog.tsx", '''"use client"

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
''')


# ============================================================
# 9. PROXY ROUTE for deployments
# ============================================================
print("\n=== 9. Deployment proxy route ===")
proxy_base = "/home/runner/workspace/plataforma-lia/src/app/api/backend-proxy"

# Create deployments route under custom-agents/[id]/deployments
deploy_route_dir = os.path.join(proxy_base, "custom-agents/[id]/deployments")
os.makedirs(deploy_route_dir, exist_ok=True)
with open(os.path.join(deploy_route_dir, "route.ts"), "w") as f:
    f.write('''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const res = await fetch(`${BACKEND_URL}/api/v1/custom-agents/${id}/deployments`, { headers: getAuthHeaders(req) })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const body = await req.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/custom-agents/${id}/deployments`, {
      method: "POST", headers: getAuthHeaders(req), body,
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')
print("  OK: proxy route for deployments")


# ============================================================
# 10. BARREL EXPORT
# ============================================================
print("\n=== 10. Barrel exports ===")
write("components/pages-agent-studio/custom-agents/index.ts", '''export { TemplateGallery } from "./TemplateGallery"
export { TemplateCard } from "./TemplateCard"
export { AgentCard } from "./AgentCard"
export { DeployDialog } from "./DeployDialog"
export type * from "./types"
''')


print(f"\\n{'=' * 60}")
print("Onda 1 foundation complete!")
print("Files created: 10 (types, store, hooks, templates, gallery, card, deploy, proxy, barrel)")
