"use client"

import { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { useLoadingWatchdog } from "@/hooks/shared/use-loading-watchdog"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import type { CompanyData } from "@/hooks/settings/department-types"
import type { CompanyBenefit } from "@/types/benefits"

export interface BlockProgress {
  filled: number
  total: number
  missingLabels: string[]
}

export interface CardBlock {
  key: string
  title: string
  subtitle?: string
  iconName: string
  fields: CardField[]
  status: "configured" | "partial" | "pending"
  progress: BlockProgress
}

export interface CardField {
  key: string
  label: string
  value: unknown
  type: "text" | "number" | "boolean" | "list" | "currency" | "time-range"
  editable: boolean
  block: string
}

interface CompanySettingsCardsState {
  blocks: CardBlock[]
  loading: boolean
  error: string | null
  successMessage: string | null
  overallProgress: number
  expandedBlocks: Set<string>
  recentlyUpdated: Set<string>
  editingField: { block: string; field: string } | null
  isSavingField: boolean
}

type BenefitItem = Partial<CompanyBenefit> & {
  id?: string
  name?: string
  category?: string
  is_active?: boolean
}

interface PipelineRules {
  min_interviews_before_offer?: number
  manager_approval_for_offer?: boolean
  max_days_in_stage?: Record<string, number>
}

interface SchedulingRules {
  allowed_days?: string[]
  allowed_hours?: { start?: string; end?: string }
  default_duration_minutes?: number
  self_scheduling_enabled?: boolean
}

interface CommunicationRules {
  auto_rejection_feedback?: boolean
  rejection_feedback_deadline_hours?: number
  preferred_channel?: string
  lia_tone?: string
}

interface AutomationRules {
  auto_screening?: boolean
  auto_scheduling?: boolean
  auto_stage_advance?: boolean
  autonomy_level?: string
}

interface ScreeningRules {
  salary_expectation_filter?: boolean
  salary_tolerance_percent?: number
  experience_policy?: string
  default_screening_questions?: string[]
}

interface HiringPolicyData {
  pipeline_rules?: PipelineRules
  scheduling_rules?: SchedulingRules
  communication_rules?: CommunicationRules
  screening_rules?: ScreeningRules
  automation_rules?: AutomationRules
  setup_progress?: number
  [key: string]: unknown
}

const ACTION_FIELD_KEYS = new Set(["import_spreadsheet", "handbook", "org_chart"])

const POLICY_FIELD_TO_BLOCK: Record<string, string> = {
  min_interviews_before_offer: "pipeline_rules",
  manager_approval_for_offer: "pipeline_rules",
  allowed_days: "scheduling_rules",
  allowed_hours: "scheduling_rules",
  default_duration_minutes: "scheduling_rules",
  self_scheduling_enabled: "scheduling_rules",
  auto_rejection_feedback: "communication_rules",
  rejection_feedback_deadline_hours: "communication_rules",
  preferred_channel: "communication_rules",
  lia_tone: "communication_rules",
  salary_expectation_filter: "screening_rules",
  salary_tolerance_percent: "screening_rules",
  experience_policy: "screening_rules",
  auto_screening: "automation_rules",
  auto_scheduling: "automation_rules",
  auto_stage_advance: "automation_rules",
  autonomy_level: "automation_rules",
}

function isFieldFilled(f: CardField): boolean {
  if (f.value === null || f.value === undefined || f.value === "") return false
  if (Array.isArray(f.value) && f.value.length === 0) return false
  return true
}

function computeBlockStatus(fields: CardField[]): "configured" | "partial" | "pending" {
  const dataFields = fields.filter(f => !ACTION_FIELD_KEYS.has(f.key))
  if (dataFields.length === 0) return "pending"
  const filled = dataFields.filter(isFieldFilled).length
  if (filled === 0) return "pending"
  if (filled === dataFields.length) return "configured"
  return "partial"
}

function computeBlockProgress(fields: CardField[]): BlockProgress {
  const dataFields = fields.filter(f => !ACTION_FIELD_KEYS.has(f.key))
  const filled = dataFields.filter(isFieldFilled).length
  const missingLabels = dataFields.filter(f => !isFieldFilled(f)).map(f => f.label)
  return { filled, total: dataFields.length, missingLabels }
}

function buildBlocks(
  company: CompanyData | null,
  benefits: BenefitItem[],
  hiringPolicy: HiringPolicyData | null,
): CardBlock[] {
  if (!company) return []

  const basicFields: CardField[] = [
    { key: "name", label: "Nome da Empresa", value: company.name, type: "text", editable: true, block: "basic" },
    { key: "tradeName", label: "Nome Fantasia", value: company.tradeName, type: "text", editable: true, block: "basic" },
    { key: "logo", label: "Logo (URL)", value: company.logo || null, type: "text", editable: true, block: "basic" },  // P1.13 audit 2026-05-20: editable=true permite paste URL externa. Upload de arquivo dedicado em backlog Sessão J.
    { key: "cnpj", label: "CNPJ", value: company.cnpj, type: "text", editable: true, block: "basic" },
    { key: "website", label: "Website", value: company.website, type: "text", editable: true, block: "basic" },
    { key: "industry", label: "Setor", value: company.industry, type: "text", editable: true, block: "basic" },
    { key: "size", label: "Porte", value: company.company_size || company.size, type: "text", editable: true, block: "basic" },
    { key: "employee_count", label: "Funcionarios", value: company.employee_count, type: "number", editable: true, block: "basic" },
    { key: "headquarters", label: "Sede", value: company.headquarters, type: "text", editable: true, block: "basic" },
    { key: "founded_year", label: "Ano de Fundacao", value: company.founded_year, type: "number", editable: true, block: "basic" },
    { key: "linkedin_url", label: "LinkedIn", value: company.linkedin_url, type: "text", editable: true, block: "basic" },
    { key: "email", label: "Email RH", value: company.email, type: "text", editable: true, block: "basic" },
    { key: "phone", label: "Telefone", value: company.phone, type: "text", editable: true, block: "basic" },
  ]

  const cultureFields: CardField[] = [
    { key: "mission", label: "Missao", value: company.mission, type: "text", editable: true, block: "culture" },
    { key: "vision", label: "Visao", value: company.vision, type: "text", editable: true, block: "culture" },
    { key: "values", label: "Valores", value: company.values, type: "list", editable: true, block: "culture" },
    { key: "work_model", label: "Modelo de Trabalho", value: company.work_model, type: "text", editable: true, block: "culture" },
    { key: "dei_initiatives", label: "DEI", value: company.dei_initiatives, type: "text", editable: true, block: "culture" },
    { key: "sustainability", label: "Sustentabilidade", value: company.sustainability, type: "text", editable: true, block: "culture" },
    { key: "social_impact", label: "Impacto Social", value: company.social_impact, type: "text", editable: true, block: "culture" },
    { key: "leadership_style", label: "Estilo de Lideranca", value: company.leadership_style, type: "text", editable: true, block: "culture" },
    { key: "growth_opportunities", label: "Oportunidades de Crescimento", value: company.growth_opportunities, type: "text", editable: true, block: "culture" },
    { key: "team_dynamics", label: "Dinamica de Equipe", value: company.team_dynamics, type: "text", editable: true, block: "culture" },
    { key: "evp_bullets", label: "EVP", value: company.evp_bullets, type: "list", editable: true, block: "culture" },
  ]

  const techFields: CardField[] = [
    { key: "tech_stack", label: "Stack Tecnologico", value: company.tech_stack, type: "list", editable: true, block: "tech" },
    { key: "engineering_culture", label: "Cultura de Engenharia", value: company.engineering_culture, type: "text", editable: true, block: "tech" },
    { key: "default_languages", label: "Idiomas", value: company.default_languages, type: "list", editable: true, block: "tech" },
  ]

  const activeBenefits = benefits.filter((b) => b.is_active !== false)
  const benefitNames = benefits.slice(0, 5).map((b) => b.name).filter(Boolean)
  const benefitsFields: CardField[] = [
    { key: "benefits_count", label: "Total de Beneficios", value: benefits.length > 0 ? `${benefits.length} cadastrado(s)` : null, type: "text", editable: false, block: "benefits" },
    { key: "benefits_active", label: "Beneficios Ativos", value: activeBenefits.length || null, type: "number", editable: false, block: "benefits" },
    { key: "benefits_list", label: "Pacote", value: benefitNames.length > 0 ? benefitNames : null, type: "list", editable: false, block: "benefits" },
  ]
  const benefitsSubtitle =
    benefits.length === 0
      ? "Nenhum benefício cadastrado"
      : `${benefits.length} cadastrado${benefits.length === 1 ? "" : "s"} · ${activeBenefits.length} ativo${activeBenefits.length === 1 ? "" : "s"}`

  const pr = hiringPolicy?.pipeline_rules
  const sr = hiringPolicy?.scheduling_rules
  const cr = hiringPolicy?.communication_rules
  const scr = hiringPolicy?.screening_rules
  const ar = hiringPolicy?.automation_rules
  const hours = sr?.allowed_hours as { start?: string; end?: string } | undefined

  const policyFields: CardField[] = [
    { key: "min_interviews_before_offer", label: "Min. Entrevistas p/ Oferta", value: pr?.min_interviews_before_offer ?? null, type: "number", editable: true, block: "policy" },
    { key: "manager_approval_for_offer", label: "Aprovacao Gestor", value: pr?.manager_approval_for_offer ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "max_days_in_stage", label: "Max. Dias por Etapa", value: pr?.max_days_in_stage ?? null, type: "text", editable: false, block: "policy" },
    { key: "allowed_days", label: "Dias Permitidos", value: sr?.allowed_days ?? null, type: "list", editable: true, block: "policy" },
    { key: "allowed_hours", label: "Horario Permitido", value: hours ? `${hours.start || ""} - ${hours.end || ""}` : null, type: "time-range", editable: true, block: "policy" },
    { key: "default_duration_minutes", label: "Duracao Padrao (min)", value: sr?.default_duration_minutes ?? null, type: "number", editable: true, block: "policy" },
    { key: "self_scheduling_enabled", label: "Auto-agendamento", value: sr?.self_scheduling_enabled ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "auto_rejection_feedback", label: "Feedback Auto Rejeicao", value: cr?.auto_rejection_feedback ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "rejection_feedback_deadline_hours", label: "Prazo Feedback Rejeicao (h)", value: cr?.rejection_feedback_deadline_hours ?? null, type: "number", editable: true, block: "policy" },
    { key: "preferred_channel", label: "Canal Preferido", value: cr?.preferred_channel ?? null, type: "text", editable: true, block: "policy" },
    { key: "lia_tone", label: "Tom da LIA", value: cr?.lia_tone ?? null, type: "text", editable: true, block: "policy" },
    { key: "salary_expectation_filter", label: "Filtro Pretensao Salarial", value: scr?.salary_expectation_filter ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "salary_tolerance_percent", label: "Tolerancia Salarial (%)", value: scr?.salary_tolerance_percent ?? null, type: "number", editable: true, block: "policy" },
    { key: "experience_policy", label: "Politica de Experiencia", value: scr?.experience_policy ?? null, type: "text", editable: true, block: "policy" },
    { key: "auto_screening", label: "Triagem Automatica", value: ar?.auto_screening ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "auto_scheduling", label: "Agendamento Automatico (Em breve)", value: ar?.auto_scheduling ?? null, type: "boolean", editable: false, block: "policy" },
    { key: "auto_stage_advance", label: "Avanco Automatico Etapas", value: ar?.auto_stage_advance ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "autonomy_level", label: "Nivel de Autonomia LIA", value: ar?.autonomy_level ?? null, type: "text", editable: true, block: "policy" },
    { key: "setup_progress", label: "Progresso Configuracao", value: hiringPolicy?.setup_progress ? `${hiringPolicy.setup_progress}%` : null, type: "text", editable: false, block: "policy" },
  ]

  const additionalData = company.additional_data
  const workforcePlan = (additionalData as Record<string, unknown> | undefined)?.workforce_plan as Record<string, unknown> | undefined
  const workforceFields: CardField[] = [
    { key: "hiring_volume", label: "Volume de Contratacao", value: additionalData?.hiring_volume ?? workforcePlan?.hiring_volume, type: "number", editable: true, block: "workforce" },
    { key: "job_types", label: "Tipos de Vaga", value: additionalData?.job_types ?? workforcePlan?.job_types, type: "list", editable: true, block: "workforce" },
    { key: "current_ats", label: "ATS Atual", value: additionalData?.current_ats ?? workforcePlan?.current_ats, type: "text", editable: true, block: "workforce" },
    { key: "main_challenges", label: "Principais Desafios", value: additionalData?.main_challenges ?? workforcePlan?.main_challenges, type: "list", editable: true, block: "workforce" },
    { key: "main_priority", label: "Prioridade Principal", value: additionalData?.main_priority ?? workforcePlan?.main_priority, type: "text", editable: true, block: "workforce" },
    { key: "communication_channels", label: "Canais de Comunicacao", value: additionalData?.communication_channels ?? workforcePlan?.communication_channels, type: "list", editable: true, block: "workforce" },
    { key: "import_spreadsheet", label: "Importar Planilha", value: null, type: "text", editable: false, block: "workforce" },
  ]

  // "documents" is renamed to "Remuneracao & Onboarding" — the upload hub
  // moved into the section cards (T#779). The remaining fields here are
  // onboarding metadata + the compensation summary; uploads of compensation
  // documents now use the contextual drop-zone embedded in this card.
  const documentFields: CardField[] = [
    { key: "onboarding_completed", label: "Onboarding Concluido", value: additionalData?.onboarding_completed_at ? "Sim" : null, type: "text", editable: false, block: "documents" },
    { key: "responsible_name", label: "Responsavel", value: additionalData?.responsible_name, type: "text", editable: true, block: "documents" },
    { key: "responsible_position", label: "Cargo do Responsavel", value: additionalData?.responsible_position, type: "text", editable: true, block: "documents" },
    { key: "additional_notes", label: "Notas Adicionais", value: additionalData?.additional_notes, type: "text", editable: true, block: "documents" },
    { key: "compensation_structure", label: "Políticas de PRV", value: company.default_salary_ranges && company.default_salary_ranges.length > 0 ? `${company.default_salary_ranges.length} faixa(s)` : null, type: "text", editable: false, block: "documents" },
  ]

  const blocks: CardBlock[] = [
    { key: "basic", title: "Dados Basicos", iconName: "Building", fields: basicFields, status: computeBlockStatus(basicFields), progress: computeBlockProgress(basicFields) },
    { key: "culture", title: "Cultura & EVP", iconName: "Heart", fields: cultureFields, status: computeBlockStatus(cultureFields), progress: computeBlockProgress(cultureFields) },
    { key: "tech", title: "Tech Stack", iconName: "Code", fields: techFields, status: computeBlockStatus(techFields), progress: computeBlockProgress(techFields) },
    { key: "benefits", title: "Benefícios", subtitle: benefitsSubtitle, iconName: "Gift", fields: benefitsFields, status: computeBlockStatus(benefitsFields), progress: computeBlockProgress(benefitsFields) },
    { key: "policy", title: "Politicas de Recrutamento", iconName: "GitBranch", fields: policyFields, status: computeBlockStatus(policyFields), progress: computeBlockProgress(policyFields) },
    { key: "workforce", title: "Workforce Planning", iconName: "BarChart3", fields: workforceFields, status: computeBlockStatus(workforceFields), progress: computeBlockProgress(workforceFields) },
    { key: "documents", title: "Remuneração Variável", iconName: "TrendingUp", fields: documentFields, status: computeBlockStatus(documentFields), progress: computeBlockProgress(documentFields) },
  ]

  return blocks
}

function snapshotFieldValues(blocks: CardBlock[]): Map<string, string> {
  const snap = new Map<string, string>()
  for (const block of blocks) {
    for (const field of block.fields) {
      snap.set(field.key, JSON.stringify(field.value))
    }
  }
  return snap
}

async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json()
    if (data?.detail) {
      return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)
    }
    if (data?.message && typeof data.message === "string") return data.message
    if (data?.error && typeof data.error === "string") return data.error
  } catch {
    /* not JSON */
  }
  if (response.status === 401 || response.status === 403) {
    return "Sessao expirada ou sem permissao. Recarregue a pagina."
  }
  if (response.status >= 500) {
    return "Backend indisponivel. Tente novamente em instantes."
  }
  return fallback
}

export function useCompanySettingsCards() {
  const [companyData, setCompanyData] = useState<CompanyData | null>(null)
  const [benefits, setBenefits] = useState<BenefitItem[]>([])
  const [hiringPolicy, setHiringPolicy] = useState<HiringPolicyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [overallProgress, setOverallProgress] = useState(0)
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set(["basic"]))
  const [recentlyUpdated, setRecentlyUpdated] = useState<Set<string>>(new Set())
  const [editingField, setEditingField] = useState<{ block: string; field: string } | null>(null)
  const [isSavingField, setIsSavingField] = useState(false)
  const [companyId, setCompanyId] = useState<string | null>(null)
  const { tenantInfo } = useCompanyId()
  // clientAccountId é o que o JWT conhece — usar em query params de benefits
  const apiCompanyId = tenantInfo?.clientAccountId || companyId || ""

  const { switchChatContext } = useLiaChatContext()
  const prevFieldSnapshotRef = useRef<Map<string, string>>(new Map())

  useLoadingWatchdog(loading, () => {
    setLoading(false)
    setError("Tempo limite de carregamento excedido")
  }, 20_000)

  const fetchCompanyProfile = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/company/profile")
      if (res.ok) {
        const data = await res.json()
        setCompanyId(data.id || null)
        return data
      }
      // T4 (#991) — backend now returns 404 (instead of silently
      // falling back to Demo Company) when the authenticated tenant
      // has no company profile yet. Surface that to the UI so the
      // onboarding modal can be triggered, and never assume the
      // returned id corresponds to the caller's tenant.
      if (res.status === 404) {
        setCompanyId(null)
        try {
          const body = await res.json()
          if (body?.detail?.code === "COMPANY_PROFILE_NOT_FOUND" && typeof window !== "undefined") {
            window.dispatchEvent(
              new CustomEvent("lia:onboarding-required", {
                detail: {
                  hintRoute: body.detail.hint_route ?? "/configuracoes/minha-empresa",
                  message: body.detail.message,
                },
              }),
            )
          }
        } catch { /* non-JSON 404 — caller still gets null */ }
      } else {
        console.error("[useCompanySettingsCards] fetchCompanyProfile HTTP", res.status, await res.text().catch(() => ""))
      }
    } catch (err) {
      console.error("[useCompanySettingsCards] fetchCompanyProfile network error:", err)
    }
    return null
  }, [])

  const fetchCultureProfile = useCallback(async (cid: string) => {
    try {
      const res = await fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(cid)}`)
      if (res.ok) return await res.json()
      // 404 is normal (profile not created yet); other statuses are real failures.
      if (res.status !== 404) {
        console.error("[useCompanySettingsCards] fetchCultureProfile HTTP", res.status, await res.text().catch(() => ""))
      }
    } catch (err) {
      console.error("[useCompanySettingsCards] fetchCultureProfile network error:", err)
    }
    return null
  }, [])

  const fetchBenefits = useCallback(async (_cidUnused: string) => {
    try {
      const res = await fetch(`/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(apiCompanyId)}`)
      if (res.ok) {
        const data = await res.json()
        return Array.isArray(data) ? data : data.items || []
      }
      console.error("[useCompanySettingsCards] fetchBenefits HTTP", res.status, await res.text().catch(() => ""))
    } catch (err) {
      console.error("[useCompanySettingsCards] fetchBenefits network error:", err)
    }
    return []
  }, [apiCompanyId])

  const fetchHiringPolicy = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/hiring-policy")
      if (res.ok) return await res.json()
      if (res.status !== 404) {
        console.error("[useCompanySettingsCards] fetchHiringPolicy HTTP", res.status, await res.text().catch(() => ""))
      }
    } catch (err) {
      console.error("[useCompanySettingsCards] fetchHiringPolicy network error:", err)
    }
    return null
  }, [])

  const fetchProgress = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/settings/progress/")
      if (res.ok) {
        const data = await res.json()
        setOverallProgress(data.overall ?? 0)
        return
      }
      console.error("[useCompanySettingsCards] fetchProgress HTTP", res.status, await res.text().catch(() => ""))
    } catch (err) {
      console.error("[useCompanySettingsCards] fetchProgress network error:", err)
    }
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const profile = await fetchCompanyProfile()
      const cid = profile?.id

      const [culture, benefitsData, policyData] = await Promise.all([
        cid ? fetchCultureProfile(cid) : null,
        cid ? fetchBenefits(cid) : [],
        fetchHiringPolicy(),
      ])

      const merged: CompanyData = {
        name: profile?.name || "",
        tradeName: profile?.trading_name || profile?.name || "",
        cnpj: profile?.cnpj || "",
        website: profile?.website || "",
        email: profile?.hr_email || profile?.main_email || "",
        phone: profile?.hr_phone || profile?.main_phone || "",
        address: profile?.address || "",
        logo: profile?.logo_url || undefined,
        industry: profile?.industry || "",
        size: profile?.size || "",
        employee_count: profile?.employee_count,
        company_size: profile?.company_size || "",
        headquarters: profile?.headquarters_city
          ? `${profile.headquarters_city}${profile.headquarters_state ? `, ${profile.headquarters_state}` : ""}`
          : culture?.headquarters || "",
        founded_year: profile?.founded_year,
        linkedin_url: profile?.linkedin_url || "",
        mission: culture?.mission || "",
        vision: culture?.vision || "",
        values: culture?.values || [],
        coreCompetencies: culture?.core_competencies || [],
        evp_bullets: culture?.evp_bullets || [],
        work_model: culture?.work_model || "",
        dei_initiatives: culture?.dei_initiatives || "",
        sustainability: culture?.sustainability || "",
        social_impact: culture?.social_impact || "",
        leadership_style: culture?.leadership_style || "",
        growth_opportunities: culture?.growth_opportunities || "",
        team_dynamics: culture?.team_dynamics || "",
        tech_stack: culture?.tech_stack || [],
        engineering_culture: culture?.engineering_culture || "",
        default_languages: culture?.default_languages || [],
        additional_data: culture?.additional_data || profile?.additional_data || undefined,
      }

      setCompanyData(merged)
      setBenefits(Array.isArray(benefitsData) ? benefitsData : [])
      setHiringPolicy(policyData)

      await fetchProgress()
    } catch {
      setError("Erro ao carregar dados da empresa")
    } finally {
      setLoading(false)
    }
  }, [fetchCompanyProfile, fetchCultureProfile, fetchBenefits, fetchHiringPolicy, fetchProgress])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const blocks = useMemo(
    () => buildBlocks(companyData, benefits, hiringPolicy),
    [companyData, benefits, hiringPolicy]
  )

  useEffect(() => {
    if (blocks.length === 0) return
    const currentSnapshot = snapshotFieldValues(blocks)
    const prevSnapshot = prevFieldSnapshotRef.current

    if (prevSnapshot.size > 0) {
      const changedKeys = new Set<string>()
      for (const [key, val] of currentSnapshot) {
        if (prevSnapshot.get(key) !== val) {
          changedKeys.add(key)
        }
      }
      if (changedKeys.size > 0) {
        setRecentlyUpdated(changedKeys)
        setTimeout(() => setRecentlyUpdated(new Set()), 2500)
      }
    }
    prevFieldSnapshotRef.current = currentSnapshot
  }, [blocks])

  useEffect(() => {
    switchChatContext("settings_config", { continuePrevious: true })
    return () => {
      switchChatContext("general", { continuePrevious: true })
    }
  }, [switchChatContext])

  // Origin guard: when this hook itself dispatches "lia:settings-updated"
  // after a save, we ALREADY call loadAll() inline. The listener exists only
  // to refresh when LIA chat / other surfaces mutate settings out-of-band.
  // Without the guard we double-load (own save + 1.5s timer reload). Track
  // the last own-dispatch timestamp and skip the refetch within 2s.
  const lastSelfDispatchRef = useRef<number>(0)
  useEffect(() => {
    const handler = (ev: Event) => {
      const detail = (ev as CustomEvent).detail as { source?: string } | undefined
      // saveField below sets source="ui" for this hook's dispatches.
      if (detail?.source === "ui" && Date.now() - lastSelfDispatchRef.current < 2000) {
        return
      }
      setTimeout(() => loadAll(), 1500)
    }
    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [loadAll])

  const toggleBlock = useCallback((blockKey: string) => {
    setExpandedBlocks(prev => {
      const next = new Set(prev)
      if (next.has(blockKey)) {
        next.delete(blockKey)
      } else {
        next.add(blockKey)
      }
      return next
    })
  }, [])

  const startEditing = useCallback((block: string, field: string) => {
    setError(null)
    setEditingField({ block, field })
  }, [])

  const cancelEditing = useCallback(() => {
    setEditingField(null)
  }, [])

  const showError = useCallback((msg: string) => {
    setError(msg)
    setTimeout(() => setError(null), 5000)
  }, [])

  // T3 (#990): canonical saveField dispatcher. Each block routes to its
  // canonical backend endpoint. Refactored from a monolithic if/else chain
  // into per-block named dispatchers for maintainability and to make the
  // "where does block X persist?" answer obvious in code review.
  // - basic    → PUT  /api/backend-proxy/company/profile/{id}
  // - culture  → PUT  /api/backend-proxy/company/culture-profile/{id}
  // - tech     → POST /api/backend-proxy/skills-catalog/company/skills-catalog (tech_stack)
  //              | PUT /culture-profile (engineering_culture, default_languages)
  // - policy   → PATCH /api/backend-proxy/hiring-policy/block (proxy translates
  //              to canonical /api/v1/company-hiring-policy/{id}/block)
  // - benefits → not field-list editable; UI uses BenefitsListSection inline.
  // - workforce → not field-list editable; UI uses WorkforceHubContent which
  //              writes to /workforce/entries (canonical). Field-list branch
  //              is dead code (guarded by MinhaEmpresaCard.tsx:328).
  // - documents → PUT /api/backend-proxy/company/profile/{id} additional_data
  //              for onboarding metadata; PRV (compensation_structure) is
  //              read-only here, edited via CompensationPoliciesListSection.
  const saveField = useCallback(async (block: string, field: string, value: unknown) => {
    if (!companyId) {
      showError("Não foi possível identificar a empresa. Recarregue a página e tente novamente.")
      setEditingField(null)
      return
    }
    setIsSavingField(true)
    setError(null)
    try {
      let response: Response | null = null
      let fallbackErr = "Falha ao salvar campo"

      const saveBasicField = async (): Promise<Response> => {
        const fieldMap: Record<string, string> = {
          name: "name",
          tradeName: "trading_name",
          cnpj: "cnpj",
          website: "website",
          industry: "industry",
          size: "company_size",
          employee_count: "employee_count",
          email: "hr_email",
          phone: "hr_phone",
          founded_year: "founded_year",
          headquarters: "headquarters_city",
          linkedin_url: "linkedin_url",
        }
        const apiField = fieldMap[field] || field
        let payload: Record<string, unknown> = { [apiField]: value }
        if (field === "headquarters" && typeof value === "string") {
          // Robust parsing: split into ≤2 parts so cities containing commas
          // (rare in BR but possible — e.g. "Brasília, Asa Sul, DF" should
          // map city="Brasília, Asa Sul" / state="DF"). Empty UF → keep prior.
          const trimmed = value.trim()
          const lastComma = trimmed.lastIndexOf(",")
          if (lastComma === -1) {
            payload = { headquarters_city: trimmed }
          } else {
            const city = trimmed.slice(0, lastComma).trim()
            const state = trimmed.slice(lastComma + 1).trim()
            payload = { headquarters_city: city, headquarters_state: state }
          }
        }
        return fetch(`/api/backend-proxy/company/profile/${companyId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
      }

      const saveCultureOrTechProfileField = async (): Promise<Response> => {
        const cultureFieldMap: Record<string, string> = {
          mission: "mission",
          vision: "vision",
          values: "values",
          work_model: "work_model",
          dei_initiatives: "dei_initiatives",
          sustainability: "sustainability",
          social_impact: "social_impact",
          leadership_style: "leadership_style",
          growth_opportunities: "growth_opportunities",
          team_dynamics: "team_dynamics",
          evp_bullets: "evp_bullets",
          engineering_culture: "engineering_culture",
          default_languages: "default_languages",
        }
        const apiField = cultureFieldMap[field] || field
        return fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [apiField]: value }),
        })
      }

      const saveTechStackField = async (): Promise<Response> => {
        // Canonical: POST /api/v1/skills-catalog/company/skills-catalog/sync
        // accepts the FULL replacement list — the inline editor sends a
        // comma-separated list, parsed already by InlineFieldEditor into
        // string[]. We use the proxy at /api/backend-proxy/skills-catalog/...
        const skills = Array.isArray(value)
          ? (value as unknown[]).map((s) => String(s).trim()).filter(Boolean)
          : typeof value === "string"
            ? value.split(",").map((s) => s.trim()).filter(Boolean)
            : []
        return fetch("/api/backend-proxy/skills-catalog/company/skills-catalog/sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tech_stack: skills }),
        })
      }

      const savePolicyField = async (): Promise<Response> => {
        const subBlock = POLICY_FIELD_TO_BLOCK[field]
        if (!subBlock) {
          throw new Error(`Campo de política não suportado para edição manual: ${field}`)
        }
        let parsedValue: unknown = value
        if (field === "allowed_hours" && typeof value === "string") {
          const m = value.match(/^\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*$/)
          if (!m) {
            throw new Error("Horário inválido. Use o formato HH:MM - HH:MM (ex.: 09:00 - 18:00).")
          }
          parsedValue = { start: m[1], end: m[2] }
        }
        // Proxy hiring-policy/block translates to canonical
        // PATCH /api/v1/company-hiring-policy/{companyId}/block.
        return fetch("/api/backend-proxy/hiring-policy/block", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ block: subBlock, data: { [field]: parsedValue } }),
        })
      }

      const saveDocumentsField = async (): Promise<Response> => {
        // Onboarding metadata fields (responsible_name, additional_notes, etc)
        // live in company.additional_data — there is no dedicated endpoint
        // and that is intentional (these are loose recruiter notes, not
        // structured business data). PRV/compensation_structure is shown
        // read-only and edited via CompensationPoliciesListSection.
        const currentAdditional = (companyData?.additional_data || {}) as Record<string, unknown>
        const nextAdditional = { ...currentAdditional, [field]: value }
        return fetch(`/api/backend-proxy/company/profile/${companyId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ additional_data: nextAdditional }),
        })
      }

      if (block === "basic") {
        response = await saveBasicField()
      } else if (block === "culture") {
        response = await saveCultureOrTechProfileField()
      } else if (block === "tech") {
        if (field === "tech_stack") {
          fallbackErr = "Falha ao salvar stack tecnológica"
          response = await saveTechStackField()
        } else {
          response = await saveCultureOrTechProfileField()
        }
      } else if (block === "policy") {
        fallbackErr = "Falha ao salvar política"
        response = await savePolicyField()
      } else if (block === "documents") {
        fallbackErr = "Falha ao salvar campo de remuneração / onboarding"
        response = await saveDocumentsField()
      } else if (block === "workforce") {
        // Workforce field-list is hidden in MinhaEmpresaCard (block.key !==
        // "workforce" guard) — edits go through WorkforceHubContent →
        // /workforce/entries. If we ever reach here, surface a clear error
        // instead of silently writing to the wrong store.
        throw new Error(
          "Edite o planejamento de workforce usando a tabela embutida no card (Workforce Planning)."
        )
      } else if (block === "benefits") {
        throw new Error(
          "Use a lista de benefícios abaixo (botão + Adicionar benefício) para criar ou editar itens."
        )
      } else {
        throw new Error(`Bloco desconhecido: ${block}`)
      }

      if (response && !response.ok) {
        const message = await extractErrorMessage(response, fallbackErr)
        throw new Error(message)
      }

      // Bidirectional UI -> chat bridge (Task #712): emit canonical events so
      // (a) the OnboardingActionOrchestrator can advance its state machine
      // when a save originates from a manual-edit card, and (b) the chat
      // context assembly can surface a silent "system note" telling LIA the
      // recruiter just edited <section>.<field>. We dispatch BOTH events here
      // explicitly (defense-in-depth) on top of the global fetch interceptor
      // in SettingsSyncBroadcaster so the bridge survives even if a hub
      // bypasses the global wrapper (e.g. via axios or background save).
      const blockToSection: Record<string, { section: string; actionId: string }> = {
        basic: { section: "profile", actionId: "configure_profile" },
        culture: { section: "culture", actionId: "configure_culture" },
        tech: { section: "tech_stack", actionId: "configure_tech_stack" },
        policy: { section: "hiring_policies", actionId: "configure_culture" },
        workforce: { section: "workforce", actionId: "configure_workforce" },
        documents: { section: "profile", actionId: "configure_profile" },
        benefits: { section: "benefits", actionId: "configure_benefits" },
      }
      const mapping = blockToSection[block]
      if (mapping && typeof window !== "undefined") {
        const detail = {
          actionId: mapping.actionId,
          section: mapping.section,
          field,
          value,
          source: "ui" as const,
          ts: Date.now(),
        }
        // Mark this dispatch as originating from us so the listener installed
        // above (lia:settings-updated) skips its own loadAll() — saveField
        // already calls loadAll() inline below. Prevents the double-fetch
        // (own save + listener 1.5s reload) that surfaced as flicker.
        lastSelfDispatchRef.current = Date.now()
        window.dispatchEvent(new CustomEvent("lia:settings-success", { detail }))
        window.dispatchEvent(new CustomEvent("lia:settings-updated", { detail }))
      }

      setSuccessMessage("Campo atualizado com sucesso!")
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadAll()
    } catch (err) {
      showError(err instanceof Error ? err.message : "Erro ao salvar campo")
    } finally {
      setIsSavingField(false)
      setEditingField(null)
    }
  }, [companyId, companyData, loadAll, showError])

  const state: CompanySettingsCardsState = {
    blocks,
    loading,
    error,
    successMessage,
    overallProgress,
    expandedBlocks,
    recentlyUpdated,
    editingField,
    isSavingField,
  }

  return {
    ...state,
    benefits,
    companyId,
    toggleBlock,
    startEditing,
    cancelEditing,
    saveField,
    refreshAll: loadAll,
  }
}
