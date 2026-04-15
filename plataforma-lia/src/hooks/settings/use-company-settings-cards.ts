"use client"

import { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import type { CompanyData } from "@/components/settings/companyTeamHub.types"

export interface CardBlock {
  key: string
  title: string
  iconName: string
  fields: CardField[]
  status: "configured" | "partial" | "pending"
}

export interface CardField {
  key: string
  label: string
  value: unknown
  type: "text" | "number" | "boolean" | "list" | "currency"
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

interface BenefitItem {
  id?: string
  name?: string
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

interface HiringPolicyData {
  pipeline_rules?: PipelineRules
  scheduling_rules?: SchedulingRules
  communication_rules?: CommunicationRules
  automation_rules?: AutomationRules
  setup_progress?: number
  [key: string]: unknown
}

const ACTION_FIELD_KEYS = new Set(["import_spreadsheet", "handbook", "org_chart"])

function computeBlockStatus(fields: CardField[]): "configured" | "partial" | "pending" {
  const dataFields = fields.filter(f => !ACTION_FIELD_KEYS.has(f.key))
  if (dataFields.length === 0) return "pending"
  const filled = dataFields.filter(f => {
    if (f.value === null || f.value === undefined || f.value === "") return false
    if (Array.isArray(f.value) && f.value.length === 0) return false
    return true
  }).length
  if (filled === 0) return "pending"
  if (filled === dataFields.length) return "configured"
  return "partial"
}

function buildBlocks(
  company: CompanyData | null,
  benefits: BenefitItem[],
  departments: unknown[],
  hiringPolicy: HiringPolicyData | null,
): CardBlock[] {
  if (!company) return []

  const basicFields: CardField[] = [
    { key: "name", label: "Nome da Empresa", value: company.name, type: "text", editable: true, block: "basic" },
    { key: "tradeName", label: "Nome Fantasia", value: company.tradeName, type: "text", editable: true, block: "basic" },
    { key: "logo", label: "Logo", value: company.logo || null, type: "text", editable: false, block: "basic" },
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
    { key: "tech_stack", label: "Stack Tecnologico", value: company.tech_stack, type: "list", editable: false, block: "tech" },
    { key: "engineering_culture", label: "Cultura de Engenharia", value: company.engineering_culture, type: "text", editable: true, block: "tech" },
    { key: "default_languages", label: "Idiomas", value: company.default_languages, type: "list", editable: true, block: "tech" },
  ]

  const activeBenefits = benefits.filter((b) => b.is_active !== false)
  const benefitNames = benefits.slice(0, 5).map((b) => b.name).filter(Boolean)
  const benefitsFields: CardField[] = [
    { key: "benefits_count", label: "Total de Beneficios", value: benefits.length > 0 ? `${benefits.length} cadastrado(s)` : null, type: "text", editable: false, block: "benefits" },
    { key: "benefits_active", label: "Beneficios Ativos", value: activeBenefits.length || null, type: "number", editable: false, block: "benefits" },
    { key: "benefits_list", label: "Pacote", value: benefitNames.length > 0 ? benefitNames : null, type: "list", editable: false, block: "benefits" },
    { key: "departments_count", label: "Departamentos", value: departments.length > 0 ? `${departments.length} cadastrado(s)` : null, type: "text", editable: false, block: "benefits" },
  ]

  const policyFields: CardField[] = hiringPolicy ? [
    { key: "min_interviews_before_offer", label: "Min. Entrevistas p/ Oferta", value: hiringPolicy.pipeline_rules?.min_interviews_before_offer, type: "number", editable: false, block: "policy" },
    { key: "manager_approval_for_offer", label: "Aprovacao Gestor", value: hiringPolicy.pipeline_rules?.manager_approval_for_offer, type: "boolean", editable: false, block: "policy" },
    { key: "self_scheduling_enabled", label: "Auto-agendamento", value: hiringPolicy.scheduling_rules?.self_scheduling_enabled, type: "boolean", editable: false, block: "policy" },
    { key: "default_duration_minutes", label: "Duracao Padrao (min)", value: hiringPolicy.scheduling_rules?.default_duration_minutes, type: "number", editable: false, block: "policy" },
    { key: "auto_rejection_feedback", label: "Feedback Auto Rejeicao", value: hiringPolicy.communication_rules?.auto_rejection_feedback, type: "boolean", editable: false, block: "policy" },
    { key: "preferred_channel", label: "Canal Preferido", value: hiringPolicy.communication_rules?.preferred_channel, type: "text", editable: false, block: "policy" },
    { key: "auto_screening", label: "Triagem Automatica", value: hiringPolicy.automation_rules?.auto_screening, type: "boolean", editable: false, block: "policy" },
    { key: "auto_stage_advance", label: "Avanco Automatico Etapas", value: hiringPolicy.automation_rules?.auto_stage_advance, type: "boolean", editable: false, block: "policy" },
    { key: "autonomy_level", label: "Nivel de Autonomia LIA", value: hiringPolicy.automation_rules?.autonomy_level, type: "text", editable: false, block: "policy" },
    { key: "setup_progress", label: "Progresso Configuracao", value: hiringPolicy.setup_progress ? `${hiringPolicy.setup_progress}%` : null, type: "text", editable: false, block: "policy" },
  ] : [
    { key: "policy_status", label: "Status", value: null, type: "text", editable: false, block: "policy" },
  ]

  const additionalData = company.additional_data
  const workforcePlan = (additionalData as Record<string, unknown> | undefined)?.workforce_plan as Record<string, unknown> | undefined
  const workforceFields: CardField[] = [
    { key: "hiring_volume", label: "Volume de Contratacao", value: additionalData?.hiring_volume ?? workforcePlan?.hiring_volume, type: "number", editable: false, block: "workforce" },
    { key: "job_types", label: "Tipos de Vaga", value: additionalData?.job_types ?? workforcePlan?.job_types, type: "list", editable: false, block: "workforce" },
    { key: "current_ats", label: "ATS Atual", value: additionalData?.current_ats ?? workforcePlan?.current_ats, type: "text", editable: false, block: "workforce" },
    { key: "main_challenges", label: "Principais Desafios", value: additionalData?.main_challenges ?? workforcePlan?.main_challenges, type: "list", editable: false, block: "workforce" },
    { key: "main_priority", label: "Prioridade Principal", value: additionalData?.main_priority ?? workforcePlan?.main_priority, type: "text", editable: false, block: "workforce" },
    { key: "communication_channels", label: "Canais de Comunicacao", value: additionalData?.communication_channels ?? workforcePlan?.communication_channels, type: "list", editable: false, block: "workforce" },
    { key: "import_spreadsheet", label: "Importar Planilha", value: null, type: "text", editable: false, block: "workforce" },
  ]

  const documentFields: CardField[] = [
    { key: "onboarding_completed", label: "Onboarding Concluido", value: additionalData?.onboarding_completed_at ? "Sim" : null, type: "text", editable: false, block: "documents" },
    { key: "responsible_name", label: "Responsavel", value: additionalData?.responsible_name, type: "text", editable: false, block: "documents" },
    { key: "responsible_position", label: "Cargo do Responsavel", value: additionalData?.responsible_position, type: "text", editable: false, block: "documents" },
    { key: "additional_notes", label: "Notas Adicionais", value: additionalData?.additional_notes, type: "text", editable: false, block: "documents" },
    { key: "handbook", label: "Manual / Handbook", value: null, type: "text", editable: false, block: "documents" },
    { key: "org_chart", label: "Organograma", value: null, type: "text", editable: false, block: "documents" },
    { key: "compensation_structure", label: "Estrutura de Remuneracao", value: company.default_salary_ranges && company.default_salary_ranges.length > 0 ? `${company.default_salary_ranges.length} faixa(s)` : null, type: "text", editable: false, block: "documents" },
  ]

  const blocks: CardBlock[] = [
    { key: "basic", title: "Dados Basicos", iconName: "Building", fields: basicFields, status: computeBlockStatus(basicFields) },
    { key: "culture", title: "Cultura & EVP", iconName: "Heart", fields: cultureFields, status: computeBlockStatus(cultureFields) },
    { key: "tech", title: "Tech Stack", iconName: "Code", fields: techFields, status: computeBlockStatus(techFields) },
    { key: "benefits", title: "Beneficios & Departamentos", iconName: "Gift", fields: benefitsFields, status: computeBlockStatus(benefitsFields) },
    { key: "policy", title: "Politicas de Recrutamento", iconName: "GitBranch", fields: policyFields, status: computeBlockStatus(policyFields) },
    { key: "workforce", title: "Workforce Planning", iconName: "BarChart3", fields: workforceFields, status: computeBlockStatus(workforceFields) },
    { key: "documents", title: "Documentos & Onboarding", iconName: "FileText", fields: documentFields, status: computeBlockStatus(documentFields) },
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

export function useCompanySettingsCards() {
  const [companyData, setCompanyData] = useState<CompanyData | null>(null)
  const [benefits, setBenefits] = useState<BenefitItem[]>([])
  const [departments, setDepartments] = useState<unknown[]>([])
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

  const { switchChatContext } = useLiaChatContext()
  const prevFieldSnapshotRef = useRef<Map<string, string>>(new Map())

  const fetchCompanyProfile = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/company/profile")
      if (res.ok) {
        const data = await res.json()
        setCompanyId(data.id || null)
        return data
      }
    } catch { /* handled by caller */ }
    return null
  }, [])

  const fetchCultureProfile = useCallback(async (cid: string) => {
    try {
      const res = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${cid}`)
      if (res.ok) return await res.json()
    } catch { /* handled by caller */ }
    return null
  }, [])

  const fetchBenefits = useCallback(async (cid: string) => {
    try {
      const res = await fetch(`/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(cid)}`)
      if (res.ok) {
        const data = await res.json()
        return Array.isArray(data) ? data : data.items || []
      }
    } catch { /* handled by caller */ }
    return []
  }, [])

  const fetchDepartments = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/company/departments")
      if (res.ok) return await res.json()
    } catch { /* handled by caller */ }
    return []
  }, [])

  const fetchHiringPolicy = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/hiring-policy")
      if (res.ok) return await res.json()
    } catch { /* handled by caller */ }
    return null
  }, [])

  const fetchProgress = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/settings/progress/")
      if (res.ok) {
        const data = await res.json()
        setOverallProgress(data.overall ?? 0)
      }
    } catch { /* handled by caller */ }
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const profile = await fetchCompanyProfile()
      const cid = profile?.id

      const [culture, benefitsData, deptsData, policyData] = await Promise.all([
        cid ? fetchCultureProfile(cid) : null,
        cid ? fetchBenefits(cid) : [],
        fetchDepartments(),
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
      setDepartments(Array.isArray(deptsData) ? deptsData : [])
      setHiringPolicy(policyData)

      await fetchProgress()
    } catch {
      setError("Erro ao carregar dados da empresa")
    } finally {
      setLoading(false)
    }
  }, [fetchCompanyProfile, fetchCultureProfile, fetchBenefits, fetchDepartments, fetchHiringPolicy, fetchProgress])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const blocks = useMemo(
    () => buildBlocks(companyData, benefits, departments, hiringPolicy),
    [companyData, benefits, departments, hiringPolicy]
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

  useEffect(() => {
    const handler = () => {
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
    setEditingField({ block, field })
  }, [])

  const cancelEditing = useCallback(() => {
    setEditingField(null)
  }, [])

  const saveField = useCallback(async (block: string, field: string, value: unknown) => {
    if (!companyId) return
    setIsSavingField(true)
    setError(null)
    try {
      let response: Response | null = null

      if (block === "basic") {
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
        if (field === "headquarters" && typeof value === "string" && value.includes(",")) {
          const parts = value.split(",").map(s => s.trim())
          payload = { headquarters_city: parts[0], headquarters_state: parts[1] || "" }
        }
        response = await fetch(`/api/backend-proxy/company/profile/${companyId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
      } else if (block === "culture" || block === "tech") {
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
        response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [apiField]: value }),
        })
      }

      if (response && !response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || "Falha ao salvar campo")
      }

      setSuccessMessage("Campo atualizado com sucesso!")
      setTimeout(() => setSuccessMessage(null), 3000)
      await loadAll()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar campo")
      setTimeout(() => setError(null), 3000)
    } finally {
      setIsSavingField(false)
      setEditingField(null)
    }
  }, [companyId, loadAll])

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
    toggleBlock,
    startEditing,
    cancelEditing,
    saveField,
    refreshAll: loadAll,
  }
}
