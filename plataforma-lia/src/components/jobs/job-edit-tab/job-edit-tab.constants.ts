import {
  Briefcase,
  Users,
  DollarSign,
  ListOrdered,
  Lock,
  Target,
  Settings,
} from "lucide-react"

export const SECTIONS = [
  {
    id: "info-geral",
    title: "Informações Gerais",
    icon: Briefcase,
    description: "Dados principais, perfil e publicação",
    fields: [
      "title", "department", "location", "workModel", "type", "level",
      "status", "priority", "urgencyLevel", "openDate", "deadline",
      "deadlineScreening", "deadlineShortlist", "deadlineClosing",
      "visibility", "isConfidential", "maskedCompanyName", "isAffirmative",
      "affirmativeCriteriaPrimary", "affirmativeCriteriaSecondary",
      "affirmativeDescription", "affirmativeDocumentRequired",
      "affirmativeDocumentTypes", "description", "targetAudience",
      "targetSector", "targetSegment", "languages", "publishedLinkedIn",
      "publishedWebsite", "publishedIndeed",
    ],
  },
  {
    id: "pessoas",
    title: "Pessoas",
    icon: Users,
    description: "Recrutador e gestor",
    fields: ["recruiter", "recruiterEmail", "manager", "managerEmail"],
  },
  {
    id: "processo",
    title: "Processo Seletivo",
    icon: ListOrdered,
    description: "Etapas do recrutamento",
    fields: ["interviewStages"],
  },
  {
    id: "remuneracao",
    title: "Remuneração",
    icon: DollarSign,
    description: "Salário, bônus e benefícios",
    fields: ["salaryMin", "salaryMax", "benefits", "variable_compensation"],
  },
]

export const SWITCH_FIELDS = [
  "publishedLinkedIn", "publishedWebsite", "publishedIndeed",
  "isConfidential", "isAffirmative", "affirmativeDocumentRequired",
]

export const LANGUAGE_OPTIONS = [
  "Inglês", "Espanhol", "Francês", "Alemão", "Italiano",
  "Mandarim", "Japonês", "Coreano", "Português", "Russo",
  "Árabe", "Hindi", "Holandês", "Sueco", "Turco", "Outro",
]

export const LEVEL_OPTIONS = [
  { value: "basico", label: "Básico" },
  { value: "intermediario", label: "Intermediário" },
  { value: "avancado", label: "Avançado" },
  { value: "fluente", label: "Fluente" },
  { value: "nativo", label: "Nativo" },
]

export const stageTypeLabels: Record<string, string> = {
  interview: "Entrevista",
  test: "Teste",
  manual: "Manual",
  automated: "Automatizado",
  hybrid: "Híbrido",
  custom: "Personalizado",
}

export const inputClass = (disabled: boolean) =>
  `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg transition-colors ${disabled ? "opacity-60 cursor-not-allowed bg-lia-bg-secondary" : ""}`

export const selectClass = (disabled: boolean) =>
  `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg transition-colors ${disabled ? "opacity-60 cursor-not-allowed bg-lia-bg-secondary" : ""}`

export const labelClass = "text-xs font-semibold text-lia-text-primary uppercase tracking-wider font-['Open_Sans',sans-serif] mb-3 block"

export const groupHeaderClass =
  "text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif] mb-3"

export function countFilledFields(
  form: Record<string, unknown>,
  fields: string[]
): number {
  return fields.filter((field) => {
    if (SWITCH_FIELDS.includes(field)) return true
    const val = form[field]
    if (val === undefined || val === null || val === "") return false
    if (Array.isArray(val)) return val.length > 0
    return true
  }).length
}

export function formatDateValue(value: unknown): string {
  if (!value) return ""
  try {
    return new Date(value as string).toISOString().split("T")[0]
  } catch {
    return ""
  }
}

export function getCategoryBadge(category?: string) {
  switch (category) {
    case "system":
      return { label: "Sistema", icon: Lock, color: "text-lia-text-tertiary bg-lia-bg-secondary/50" }
    case "default":
      return { label: "Padrão", icon: Target, color: "text-wedo-cyan-dark bg-wedo-cyan/10" }
    case "custom":
      return { label: "Custom", icon: Settings, color: "text-status-warning bg-status-warning/10" }
    default:
      return { label: "Custom", icon: Settings, color: "text-status-warning bg-status-warning/10" }
  }
}
