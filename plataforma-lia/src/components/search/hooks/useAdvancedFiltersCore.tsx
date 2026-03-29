"use client"


import { useState, useCallback, useEffect, useMemo, useRef } from "react"
import { 
  X, Settings, MapPin, Briefcase, Building2, Code, GraduationCap, 
  Globe, ChevronRight, Search, RotateCcw, Zap, Mail, Phone, Clock,
  RefreshCw, Filter, AlertCircle, TrendingUp, Save, FolderOpen, History,
  Bookmark, ChevronDown, Check, Home, Crown, Rocket, UserCheck, Eye, HelpCircle,
  Brain, Loader2, Info, List, ArrowUpDown
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { CreditConfirmationDialog } from "../credit-confirmation-dialog"
import { calculateCreditsLocally, CreditEstimate } from "@/lib/api/candidate-search"
import { SkillsFilterInput, SkillItem } from "../SkillsFilterInput"
import { ExpertiseAreasInput } from "../ExpertiseAreasInput"
import { CompanyFilterInput, CompanyItem, CompanyTimeFilter } from "../CompanyFilterInput"
import { ExcludedCompaniesInput, ExcludedCompanyItem, ExcludedTimeFilter } from "../ExcludedCompaniesInput"
import { IndustryFilterInput, IndustryTimeFilter } from "../IndustryFilterInput"
import { CompanyTagsInput, CompanyTagItem, CompanyTagsTimeFilter } from "../CompanyTagsInput"
import { CompanyHQLocationsInput, CompanyHQTimeFilter } from "../CompanyHQLocationsInput"
import { FundingStagesInput } from "../FundingStagesInput"
import { UniversitiesFilterInput } from "../UniversitiesFilterInput"
import { ExcludedUniversitiesInput } from "../ExcludedUniversitiesInput"
import { UniversityLocationsInput } from "../UniversityLocationsInput"
import { DegreeRequirementsInput } from "../DegreeRequirementsInput"
import { FieldsOfStudyInput } from "../FieldsOfStudyInput"
import { GraduationYearInput } from "../GraduationYearInput"
import { LanguageFilterInput } from "../LanguageFilterInput"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

export type SaveDestination = "talent_funnel" | "search_history" | "saved_searches"
export type SearchSource = "local" | "global" | "hybrid"

const saveDestinations: { 
  key: SaveDestination
  label: string
  description: string
  icon: React.ElementType 
}[] = [
  { 
    key: "talent_funnel", 
    label: "Funil de Talentos", 
    description: "Adicionar candidatos ao funil de uma vaga",
    icon: FolderOpen 
  },
  { 
    key: "search_history", 
    label: "Histórico de Buscas", 
    description: "Salvar automaticamente no histórico",
    icon: History 
  },
  { 
    key: "saved_searches", 
    label: "Buscas Salvas", 
    description: "Favoritar para reutilizar depois",
    icon: Bookmark 
  },
]

export type HideViewedScope = 
  | "dont_hide"
  | "by_you_this_project"
  | "by_you_all_projects"
  | "shortlisted_by_you"
  | "by_org_this_project"
  | "by_org_all_projects"
  | "shortlisted_org_this_project"
  | "shortlisted_org_all_projects"

export type HideViewedPeriod = 
  | "all_time"
  | "last_24h"
  | "last_2_weeks"
  | "last_3_months"
  | "last_6_months"

export interface SearchFilters {
  ppiOptions?: {
    searchType?: "fast" | "pro"
    highFreshness?: boolean
    strictFilters?: boolean
    requireEmails?: boolean
    showEmails?: boolean
    requirePhoneNumbers?: boolean
    showPhoneNumbers?: boolean
    requirePhonesOrEmails?: boolean
    openToWorkOnly?: boolean
  }
  searchOptions?: {
    includeDiscovered?: boolean
  }
  general?: {
    minExperience?: number
    maxExperience?: number
    hideViewedProfiles?: boolean
    hideViewedScope?: HideViewedScope
    hideViewedPeriod?: HideViewedPeriod
  }
  job?: {
    titles?: string[]
    titleScope?: "current_only" | "current_recent" | "current_past"
    pastTitles?: string[]
    levels?: string[]
    roles?: string[]
    timeInRoleMin?: string
    timeInRoleMax?: string
    minAverageTenure?: string
  }
  company?: {
    companyItems?: CompanyItem[]
    companyTimeFilter?: CompanyTimeFilter
    specificYears?: { start: number; end: number }
    fundingStages?: string[]
    excludedCompanyItems?: ExcludedCompanyItem[]
    excludedTimeFilter?: ExcludedTimeFilter
    excludeDNC?: boolean
    industries?: string[]
    industryTimeFilter?: IndustryTimeFilter
    companyTags?: CompanyTagItem[]
    companyTagsTimeFilter?: CompanyTagsTimeFilter
    companyHQLocations?: string[]
    companyHQTimeFilter?: CompanyHQTimeFilter
    companySizes?: string[]
    companyFoundedAfter?: number
  }
  skills?: {
    skillItems?: SkillItem[]
    expertise?: string[]
  }
  education?: {
    universities?: string[]
    excludedUniversities?: string[]
    universityLocations?: string[]
    degreeRequirementMode?: 'regular' | 'nested'
    degree?: string | null
    degrees?: string[]
    fieldsOfStudyMode?: 'regular' | 'nested'
    fieldsOfStudy?: string[]
    graduationYearMin?: number | null
    graduationYearMax?: number | null
  }
  languages?: {
    languages?: string[]
    proficiencyLevel?: string
  }
  profile?: {
    isDecisionMaker?: boolean
    isTopUniversities?: boolean
    isStartup?: boolean
  }
}

export function convertToPearchFilters(filters: SearchFilters): {
  customFilters: Record<string, any>
  apiOptions: Record<string, any>
  hideViewedOptions?: {
    enabled: boolean
    scope: HideViewedScope
    period: HideViewedPeriod
  }
} {
  const customFilters: Record<string, any> = {}
  const apiOptions: Record<string, any> = {}

  if (filters.ppiOptions) {
    apiOptions.type = filters.ppiOptions.searchType || "fast"
    apiOptions.high_freshness = filters.ppiOptions.highFreshness || false
    apiOptions.strict_filters = filters.ppiOptions.strictFilters || false
    apiOptions.require_emails = filters.ppiOptions.requireEmails || false
    apiOptions.show_emails = filters.ppiOptions.showEmails || false
    apiOptions.require_phone_numbers = filters.ppiOptions.requirePhoneNumbers || false
    apiOptions.show_phone_numbers = filters.ppiOptions.showPhoneNumbers || false
    apiOptions.require_phones_or_emails = filters.ppiOptions.requirePhonesOrEmails || false
  }

  const hideViewedOptions = filters.general?.hideViewedScope && filters.general.hideViewedScope !== "dont_hide" 
    ? {
        enabled: true,
        scope: filters.general.hideViewedScope,
        period: filters.general.hideViewedPeriod || "all_time"
      }
    : undefined

  if (filters.job?.titles?.length) {
    customFilters.titles = filters.job.titles
    customFilters.title_scope = filters.job.titleScope || "current_only"
  }
  if (filters.job?.pastTitles?.length) {
    customFilters.past_titles = filters.job.pastTitles
  }
  if (filters.job?.levels?.length) {
    customFilters.seniority_levels = filters.job.levels
  }
  if (filters.job?.roles?.length) {
    customFilters.job_functions = filters.job.roles
  }
  if (filters.job?.timeInRoleMin || filters.job?.timeInRoleMax) {
    const timeValues: Record<string, number> = {
      "3_months": 3, "6_months": 6, "1_year": 12, "1.5_years": 18,
      "2_years": 24, "3_years": 36, "5_years": 60, "7_years": 84,
      "10_years": 120, "15_years": 180
    }
    const minTime = filters.job.timeInRoleMin !== "no_limit" ? filters.job.timeInRoleMin : undefined
    const maxTime = filters.job.timeInRoleMax !== "no_limit" ? filters.job.timeInRoleMax : undefined
    const minVal = minTime ? timeValues[minTime] || 0 : 0
    const maxVal = maxTime ? timeValues[maxTime] || 999 : 999
    if (minVal <= maxVal) {
      if (minTime) customFilters.time_in_role_min = minTime
      if (maxTime) customFilters.time_in_role_max = maxTime
    }
  }
  if (filters.job?.minAverageTenure && filters.job.minAverageTenure !== "no_limit") {
    customFilters.min_average_tenure = filters.job.minAverageTenure
  }

  if (filters.company?.companyItems?.length) {
    const companyNames = filters.company.companyItems.map(c => c.name)
    const timeFilter = filters.company.companyTimeFilter || 'current_past'
    
    switch (timeFilter) {
      case 'current_only':
        customFilters.current_employer = companyNames
        break
      case 'past_only':
        customFilters.past_employer = companyNames
        break
      case 'current_past':
        customFilters.current_employer = companyNames
        customFilters.past_employer = companyNames
        break
      case 'specific_years':
        customFilters.current_employer = companyNames
        customFilters.past_employer = companyNames
        if (filters.company.specificYears) {
          customFilters.company_years_start = filters.company.specificYears.start
          customFilters.company_years_end = filters.company.specificYears.end
        }
        break
      case 'funding_stage':
        customFilters.current_employer = companyNames
        customFilters.past_employer = companyNames
        if (filters.company.fundingStages?.length) {
          customFilters.funding_stages = filters.company.fundingStages
        }
        break
    }
  }

  if (filters.company?.excludedCompanyItems?.length) {
    const excludedNames = filters.company.excludedCompanyItems.map(c => c.name)
    const excludedTimeFilter = filters.company.excludedTimeFilter || 'current_only'
    
    if (excludedTimeFilter === 'current_only') {
      customFilters.exclude_current_employer = excludedNames
    } else {
      customFilters.exclude_companies = excludedNames
    }
  }

  if (filters.company?.excludeDNC) {
    customFilters.exclude_dnc = true
  }

  if (filters.company?.industries?.length) {
    customFilters.industries = filters.company.industries
    if (filters.company.industryTimeFilter) {
      customFilters.industry_time_filter = filters.company.industryTimeFilter
    }
  }
  if (filters.company?.companyTags?.length) {
    customFilters.company_tags = filters.company.companyTags.map(t => t.name)
    if (filters.company.companyTagsTimeFilter) {
      customFilters.company_tags_time_filter = filters.company.companyTagsTimeFilter
    }
  }
  if (filters.company?.companyHQLocations?.length) {
    customFilters.company_hq_locations = filters.company.companyHQLocations
    if (filters.company.companyHQTimeFilter) {
      customFilters.company_hq_time_filter = filters.company.companyHQTimeFilter
    }
  }
  if (filters.company?.companySizes?.length) {
    customFilters.company_sizes = filters.company.companySizes
  }
  if (filters.company?.companyFoundedAfter) {
    customFilters.company_founded_after = filters.company.companyFoundedAfter
  }
  if (filters.company?.fundingStages?.length) {
    customFilters.company_funding_stages = filters.company.fundingStages
  }

  if (filters.skills?.skillItems?.length) {
    const pinnedSkills = filters.skills.skillItems.filter(s => s.isPinned).map(s => s.name)
    const regularSkills = filters.skills.skillItems.filter(s => !s.isPinned).map(s => s.name)
    
    if (pinnedSkills.length > 0) {
      customFilters.must_have_skills = pinnedSkills
    }
    if (regularSkills.length > 0) {
      customFilters.skills = regularSkills
    }
  }

  if (filters.education?.universities?.length) {
    customFilters.universities = filters.education.universities
  }
  if (filters.education?.degrees?.length) {
    customFilters.degrees = filters.education.degrees
  }
  if (filters.education?.fieldsOfStudy?.length) {
    customFilters.fields_of_study = filters.education.fieldsOfStudy
  }

  if (filters.languages?.languages?.length) {
    customFilters.languages = filters.languages.languages
  }

  // Profile indicators (all free)
  if (filters.ppiOptions?.openToWorkOnly) {
    customFilters.is_opentowork = true
  }
  if (filters.profile?.isDecisionMaker) {
    customFilters.is_decision_maker = true
  }
  if (filters.profile?.isTopUniversities) {
    customFilters.is_top_universities = true
  }
  if (filters.profile?.isStartup) {
    customFilters.company_is_startup = true
  }

  // Expertise
  if (filters.skills?.expertise?.length) {
    customFilters.expertise = filters.skills.expertise
  }

  return { customFilters, apiOptions, hideViewedOptions }
}

export function normalizeFiltersFromServer(filters: SearchFilters & Record<string, any>): SearchFilters {
  const normalized: SearchFilters & Record<string, any> = JSON.parse(JSON.stringify(filters))
  
  if (!normalized.company) {
    normalized.company = {}
  }
  
  if (normalized.company_funding_stages && !normalized.company.fundingStages) {
    normalized.company.fundingStages = normalized.company_funding_stages
  }
  
  if (normalized.company_tags && !normalized.company.companyTags) {
    const tags = Array.isArray(normalized.company_tags) 
      ? normalized.company_tags.map((t: string | { name: string }) => 
          typeof t === 'string' ? { name: t } : t
        )
      : []
    normalized.company.companyTags = tags
  }
  
  if (normalized.company_hq_locations && !normalized.company.companyHQLocations) {
    normalized.company.companyHQLocations = normalized.company_hq_locations
  }
  
  if (normalized.company_sizes && !normalized.company.companySizes) {
    normalized.company.companySizes = normalized.company_sizes
  }
  
  if (normalized.industries && !normalized.company.industries) {
    normalized.company.industries = normalized.industries
  }
  
  if (normalized.industry_time_filter && !normalized.company.industryTimeFilter) {
    normalized.company.industryTimeFilter = normalized.industry_time_filter
  }
  
  if (normalized.company_tags_time_filter && !normalized.company.companyTagsTimeFilter) {
    normalized.company.companyTagsTimeFilter = normalized.company_tags_time_filter
  }
  
  if (normalized.company_hq_time_filter && !normalized.company.companyHQTimeFilter) {
    normalized.company.companyHQTimeFilter = normalized.company_hq_time_filter
  }
  
  const { 
    company_funding_stages, company_tags, company_hq_locations, 
    company_sizes, industries, industry_time_filter,
    company_tags_time_filter, company_hq_time_filter,
    ...cleanedFilters 
  } = normalized
  
  return cleanedFilters as SearchFilters
}

interface AdvancedFiltersModalProps {
  isOpen: boolean
  onClose: () => void
  onApply: (filters: SearchFilters, options?: { searchSource?: SearchSource }) => void
  onSave?: (filters: SearchFilters, destination: SaveDestination) => void
  initialFilters?: SearchFilters
  estimatedMatches?: number
  candidateLimit?: number
  defaultSaveDestination?: SaveDestination
  sortBy?: string
  onSortByChange?: (value: string) => void
}

type FilterCategory = 
  | "ppiOptions"
  | "general" 
  | "job" 
  | "company" 
  | "skills" 
  | "education" 
  | "languages"
  | "profile"

const categories: { key: FilterCategory; label: string; icon: React.ElementType; description?: string }[] = [
  { key: "ppiOptions", label: "Opções de Busca", icon: Zap, description: "Controle de qualidade e custo" },
  { key: "general", label: "Geral", icon: Settings, description: "Experiência e perfis" },
  { key: "profile", label: "Perfil Profissional", icon: UserCheck, description: "Indicadores de perfil" },
  { key: "job", label: "Cargo", icon: Briefcase, description: "Títulos e níveis" },
  { key: "company", label: "Empresa", icon: Building2, description: "Empresas e setores" },
  { key: "skills", label: "Habilidades", icon: Code, description: "Skills técnicas" },
  { key: "education", label: "Formação", icon: GraduationCap, description: "Universidades e cursos" },
  { key: "languages", label: "Idiomas", icon: Globe, description: "Línguas e proficiência" },
]

const experienceLevels = [
  { value: "owner", label: "Proprietário" },
  { value: "partner", label: "Sócio" },
  { value: "c-level", label: "C-Level" },
  { value: "vp", label: "Vice-Presidente" },
  { value: "director", label: "Diretor" },
  { value: "manager", label: "Gerente" },
  { value: "mid-senior", label: "Sênior" },
  { value: "associate", label: "Pleno" },
  { value: "entry", label: "Júnior" },
  { value: "intern", label: "Estagiário" },
  { value: "trainee", label: "Trainee" }
]

const jobRoles = [
  { value: "engineering", label: "Engenharia" },
  { value: "product", label: "Produto" },
  { value: "design", label: "Design" },
  { value: "data", label: "Dados & Analytics" },
  { value: "marketing", label: "Marketing" },
  { value: "sales", label: "Comercial/Vendas" },
  { value: "customer_success", label: "Sucesso do Cliente" },
  { value: "finance", label: "Finanças" },
  { value: "hr", label: "Recursos Humanos" },
  { value: "legal", label: "Jurídico" },
  { value: "operations", label: "Operações" },
  { value: "it", label: "TI/Infraestrutura" },
  { value: "health", label: "Saúde" },
  { value: "education", label: "Educação" },
  { value: "media", label: "Mídia/Conteúdo" }
]

const titleScopeOptions = [
  { value: "current_only", label: "Cargo Atual", description: "Pessoas com este cargo atualmente" },
  { value: "current_recent", label: "Atual + Recente", description: "Cargo atual ou nos últimos 2 anos" },
  { value: "current_past", label: "Atual + Histórico", description: "Cargo em qualquer ponto da carreira" }
]

const timeInRoleOptions = [
  { value: "no_limit", label: "Sem limite" },
  { value: "3_months", label: "3 meses" },
  { value: "6_months", label: "6 meses" },
  { value: "1_year", label: "1 ano" },
  { value: "1.5_years", label: "1,5 anos" },
  { value: "2_years", label: "2 anos" },
  { value: "3_years", label: "3 anos" },
  { value: "5_years", label: "5 anos" },
  { value: "7_years", label: "7 anos" },
  { value: "10_years", label: "10 anos" },
  { value: "15_years", label: "15 anos" }
]

const tenureOptions = [
  { value: "no_limit", label: "Selecionar duração" },
  { value: "6_months", label: "6 meses" },
  { value: "1_year", label: "1 ano" },
  { value: "1.5_years", label: "1,5 anos" },
  { value: "2_years", label: "2 anos" },
  { value: "3_years", label: "3 anos" },
  { value: "5_years", label: "5 anos" },
  { value: "7_years", label: "7 anos" },
  { value: "10_years", label: "10 anos" }
]


const companySizes = [
  { value: "emerging", label: "Emergente (até 50 funcionários)" },
  { value: "small", label: "Pequena (51-200 funcionários)" },
  { value: "mid-sized", label: "Média (201-500 funcionários)" },
  { value: "growing", label: "Em Crescimento (501-1000 funcionários)" },
  { value: "large", label: "Grande (1001-5000 funcionários)" },
  { value: "enterprise", label: "Corporação (5001-10000 funcionários)" },
  { value: "large-enterprise", label: "Grande Corporação (10001+)" }
]

const degreeTypes = [
  { value: "high-school", label: "Ensino Médio" },
  { value: "associate", label: "Tecnólogo" },
  { value: "bachelor", label: "Graduação" },
  { value: "master", label: "Mestrado" },
  { value: "phd", label: "Doutorado" },
  { value: "mba", label: "MBA" }
]

const proficiencyLevels = [
  { value: "any", label: "Qualquer nível" },
  { value: "native", label: "Nativo" },
  { value: "fluent", label: "Fluente" },
  { value: "professional", label: "Profissional" },
  { value: "intermediate", label: "Intermediário" },
  { value: "basic", label: "Básico" }
]

const hideViewedScopeOptions: { value: HideViewedScope; label: string; description?: string; isShortlisted?: boolean }[] = [
  { value: "dont_hide", label: "Não ocultar perfis", description: "Mostrar todos os perfis" },
  { value: "by_you_this_project", label: "Visualizados por você neste projeto", description: "Apenas visualizados por você nesta vaga" },
  { value: "by_you_all_projects", label: "Visualizados por você em todos os projetos", description: "Visualizados por você em qualquer vaga" },
  { value: "shortlisted_by_you", label: "Shortlistados por você", description: "Candidatos que você entrevistou", isShortlisted: true },
  { value: "by_org_this_project", label: "Visualizados pela organização neste projeto", description: "Visualizados por qualquer colega nesta vaga" },
  { value: "by_org_all_projects", label: "Visualizados pela organização em todos os projetos", description: "Visualizados por qualquer colega em qualquer vaga" },
  { value: "shortlisted_org_this_project", label: "Shortlistados pela organização neste projeto", description: "Candidatos entrevistados por qualquer colega nesta vaga", isShortlisted: true },
  { value: "shortlisted_org_all_projects", label: "Shortlistados pela organização em todos os projetos", description: "Candidatos entrevistados por qualquer colega em qualquer vaga", isShortlisted: true },
]

const hideViewedPeriodOptions: { value: HideViewedPeriod; label: string }[] = [
  { value: "all_time", label: "Todo o período" },
  { value: "last_24h", label: "Últimas 24 horas" },
  { value: "last_2_weeks", label: "Últimas 2 semanas" },
  { value: "last_3_months", label: "Últimos 3 meses" },
  { value: "last_6_months", label: "Últimos 6 meses" },
]

const SectionHeader = ({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description?: string }) => (
  <div className="flex items-center gap-2 mb-4">
    <Icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
    <div>
      <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
      {description && <p className="text-xs text-gray-500">{description}</p>}
    </div>
  </div>
)


export function useAdvancedFiltersCore(props: AdvancedFiltersModalProps) {
  const {
    isOpen,
    onClose,
    onApply,
    onSave,
    initialFilters = {},
    estimatedMatches,
    candidateLimit = 15,
    defaultSaveDestination = "search_history",
    sortBy = 'relevance',
    onSortByChange
  } = props
  const [filters, setFilters] = useState<SearchFilters>(initialFilters)
  const [saveDestination, setSaveDestination] = useState<SaveDestination>(defaultSaveDestination)
  const [isDestinationOpen, setIsDestinationOpen] = useState(false)
  const [searchSource, setSearchSource] = useState<SearchSource>("local")
  const isLocalSearch = searchSource === "local"
  const [showCreditConfirm, setShowCreditConfirm] = useState(false)
  const [pendingSearch, setPendingSearch] = useState<(() => void) | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [activeSection, setActiveSection] = useState<string>("searchSource")

  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({
    searchSource: null,
    ppiOptions: null,
    general: null,
    profile: null,
    job: null,
    company: null,
    skills: null,
    education: null,
    languages: null
  })

  const sidebarCategories = [
    { key: "searchSource", label: "Origem da Busca", icon: Search },
    { key: "ppiOptions", label: "Opções de Busca", icon: Settings },
    { key: "general", label: "Geral", icon: Settings },
    { key: "profile", label: "Perfil Profissional", icon: UserCheck },
    { key: "job", label: "Cargo", icon: Briefcase },
    { key: "company", label: "Empresa", icon: Building2 },
    { key: "skills", label: "Habilidades", icon: Code },
    { key: "education", label: "Formação", icon: GraduationCap },
    { key: "languages", label: "Idiomas", icon: Globe },
  ]

  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    const observers: IntersectionObserver[] = []
    const visibleSections = new Set<string>()

    Object.keys(sectionRefs.current).forEach((sectionKey) => {
      const element = sectionRefs.current[sectionKey]
      if (!element) return

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              visibleSections.add(sectionKey)
            } else {
              visibleSections.delete(sectionKey)
            }
            const orderedSections = sidebarCategories.map(c => c.key)
            for (const section of orderedSections) {
              if (visibleSections.has(section)) {
                setActiveSection(section)
                break
              }
            }
          })
        },
        {
          root: container,
          rootMargin: "-20% 0px -70% 0px",
          threshold: 0
        }
      )

      observer.observe(element)
      observers.push(observer)
    })

    return () => {
      observers.forEach((observer) => observer.disconnect())
    }
  }, [isOpen])

  const scrollToSection = useCallback((sectionKey: string) => {
    const element = sectionRefs.current[sectionKey]
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      const normalizedFilters = normalizeFiltersFromServer(initialFilters)
      setFilters(normalizedFilters)
    }
  }, [isOpen, initialFilters])

  const updateFilter = useCallback(<T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string | string[] | number | boolean | null
  ) => {
    setFilters(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }))
  }, [])

  const addToArray = useCallback(<T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string
  ) => {
    if (!value.trim()) return
    setFilters(prev => {
      const categoryObj = prev[category] as Record<string, unknown> | undefined
      const currentArray = (categoryObj?.[key as string] as string[]) || []
      if (currentArray.includes(value.trim())) return prev
      return {
        ...prev,
        [category]: {
          ...prev[category],
          [key]: [...currentArray, value.trim()]
        }
      }
    })
  }, [])

  const removeFromArray = useCallback(<T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string
  ) => {
    setFilters(prev => {
      const categoryObj = prev[category] as Record<string, unknown> | undefined
      const currentArray = (categoryObj?.[key as string] as string[]) || []
      return {
        ...prev,
        [category]: {
          ...prev[category],
          [key]: currentArray.filter((v: string) => v !== value)
        }
      }
    })
  }, [])

  const resetFilters = useCallback(() => {
    setFilters({})
    setSearchSource("local")
  }, [])

  const handleApply = useCallback(() => {
    if (searchSource === "global" || searchSource === "hybrid") {
      setPendingSearch(() => () => {
        onApply(filters, { searchSource })
      })
      setShowCreditConfirm(true)
    } else {
      onApply(filters, { searchSource })
    }
  }, [filters, searchSource, onApply])

  const handleConfirmSearch = useCallback(() => {
    setIsSearching(true)
    if (pendingSearch) {
      pendingSearch()
    }
    setShowCreditConfirm(false)
    setPendingSearch(null)
    setIsSearching(false)
  }, [pendingSearch])

  const getActiveFiltersCount = useCallback(() => {
    let count = 0
    Object.values(filters).forEach(category => {
      if (category) {
        Object.values(category).forEach(value => {
          if (value !== undefined && value !== null && value !== "" && value !== false &&
              !(Array.isArray(value) && value.length === 0)) {
            count++
          }
        })
      }
    })
    return count
  }, [filters])

  const creditEstimate = useMemo((): CreditEstimate => {
    const opts = filters.ppiOptions || {}
    return calculateCreditsLocally({
      searchType: opts.searchType || "fast",
      limit: candidateLimit,
      highFreshness: opts.highFreshness || false,
      requireEmails: opts.requireEmails || false,
      showEmails: opts.showEmails || false,
      requirePhoneNumbers: opts.requirePhoneNumbers || false,
      showPhoneNumbers: opts.showPhoneNumbers || false,
      requirePhonesOrEmails: opts.requirePhonesOrEmails || false
    })
  }, [filters.ppiOptions, candidateLimit])



  return {
    activeSection,
    candidateLimit,
    addToArray,
    creditEstimate,
    filters,
    getActiveFiltersCount,
    handleApply,
    handleConfirmSearch,
    isDestinationOpen,
    isLocalSearch,
    isSearching,
    onClose,
    onSave,
    removeFromArray,
    resetFilters,
    saveDestination,
    scrollContainerRef,
    scrollToSection,
    searchSource,
    sectionRefs,
    setFilters,
    setIsDestinationOpen,
    setSaveDestination,
    setSearchSource,
    setShowCreditConfirm,
    showCreditConfirm,
    sidebarCategories,
    updateFilter,
  }
}
