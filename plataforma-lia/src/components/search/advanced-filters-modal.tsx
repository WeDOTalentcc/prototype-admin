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
import { CreditConfirmationDialog } from "./credit-confirmation-dialog"
import { calculateCreditsLocally, CreditEstimate } from "@/lib/api/candidate-search"
import { SkillsFilterInput, SkillItem } from "./SkillsFilterInput"
import { ExpertiseAreasInput } from "./ExpertiseAreasInput"
import { CompanyFilterInput, CompanyItem, CompanyTimeFilter } from "./CompanyFilterInput"
import { ExcludedCompaniesInput, ExcludedCompanyItem, ExcludedTimeFilter } from "./ExcludedCompaniesInput"
import { IndustryFilterInput, IndustryTimeFilter } from "./IndustryFilterInput"
import { CompanyTagsInput, CompanyTagItem, CompanyTagsTimeFilter } from "./CompanyTagsInput"
import { CompanyHQLocationsInput, CompanyHQTimeFilter } from "./CompanyHQLocationsInput"
import { FundingStagesInput } from "./FundingStagesInput"
import { UniversitiesFilterInput } from "./UniversitiesFilterInput"
import { ExcludedUniversitiesInput } from "./ExcludedUniversitiesInput"
import { UniversityLocationsInput } from "./UniversityLocationsInput"
import { DegreeRequirementsInput } from "./DegreeRequirementsInput"
import { FieldsOfStudyInput } from "./FieldsOfStudyInput"
import { GraduationYearInput } from "./GraduationYearInput"
import { LanguageFilterInput } from "./LanguageFilterInput"
import { useSemanticSearch } from "@/hooks/useSemanticSearch"
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

const globalJobPresets = [
  { 
    id: "customer_success", 
    name: "Sucesso do Cliente", 
    description: "Funções de sucesso do cliente e suporte",
    titles: ["Customer Success Manager", "Senior Customer Success Manager", "Customer Success Specialist", "Customer Support Specialist", "Customer Success Engineer", "Solutions Engineer", "Technical Account Manager", "Director of Customer Success", "Vice President of Customer Success", "Head of Customer Success"]
  },
  { 
    id: "data_analytics", 
    name: "Dados & Analytics", 
    description: "Ciência de dados, analytics e engenharia de dados",
    titles: ["Data Scientist", "Senior Data Scientist", "Machine Learning Engineer", "Senior Machine Learning Engineer", "Data Analyst", "Senior Data Analyst", "Data Engineer", "Senior Data Engineer", "Analytics Engineer", "Head of Data"]
  },
  { 
    id: "design", 
    name: "Design", 
    description: "Design de produto, UX/UI e liderança de design",
    titles: ["Product Designer", "Senior Product Designer", "UX Designer", "UI Designer", "UX Researcher", "Design Lead", "Head of Design", "Vice President of Design", "Design Director", "Creative Director", "Brand Designer"]
  },
  { 
    id: "devops", 
    name: "DevOps & Infraestrutura", 
    description: "DevOps, SRE e engenharia de infraestrutura",
    titles: ["DevOps Engineer", "Senior DevOps Engineer", "Site Reliability Engineer", "SRE", "Platform Engineer", "Senior Platform Engineer", "Systems Engineer", "Infrastructure Engineer", "Cloud Engineer", "Head of Infrastructure"]
  },
  { 
    id: "engineering", 
    name: "Engenharia de Software", 
    description: "Desenvolvimento de software e liderança técnica",
    titles: ["Software Engineer", "Senior Software Engineer", "Staff Software Engineer", "Principal Software Engineer", "Frontend Developer", "Backend Developer", "Fullstack Developer", "Tech Lead", "Engineering Manager", "Director of Engineering", "VP of Engineering", "CTO"]
  },
  { 
    id: "product", 
    name: "Produto", 
    description: "Gestão de produto e estratégia",
    titles: ["Product Manager", "Senior Product Manager", "Group Product Manager", "Director of Product", "Vice President of Product", "Head of Product", "Chief Product Officer", "Product Owner", "Technical Product Manager"]
  },
  { 
    id: "sales", 
    name: "Comercial & Vendas", 
    description: "Vendas, desenvolvimento de negócios e parcerias",
    titles: ["Sales Representative", "Account Executive", "Senior Account Executive", "Sales Manager", "Sales Director", "Vice President of Sales", "Business Development Representative", "BDR", "SDR", "Head of Sales", "Chief Revenue Officer"]
  },
  { 
    id: "marketing", 
    name: "Marketing", 
    description: "Marketing digital, growth e comunicação",
    titles: ["Marketing Manager", "Senior Marketing Manager", "Marketing Director", "Head of Marketing", "VP of Marketing", "CMO", "Growth Marketing Manager", "Digital Marketing Specialist", "Content Marketing Manager", "Brand Manager"]
  }
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

import { useAdvancedFiltersCore } from './hooks/useAdvancedFiltersCore'
import { JobFiltersSection } from './JobFiltersSection'

export function AdvancedFiltersModal(props: AdvancedFiltersModalProps) {
  const { isOpen } = props
  const {
    activeSection, addToArray, candidateLimit, creditEstimate, filters, getActiveFiltersCount, handleApply, handleConfirmSearch,
    isDestinationOpen, isLocalSearch, isSearching, onClose, onSave, removeFromArray, resetFilters,
    saveDestination, scrollContainerRef, scrollToSection, searchSource, sectionRefs, setFilters, setIsDestinationOpen, setSaveDestination,
    setSearchSource, setShowCreditConfirm, showCreditConfirm, sidebarCategories, updateFilter,
  } = useAdvancedFiltersCore(props)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-[1px]"
        onClick={onClose}
      />
      
      <div 
        className="relative w-full max-w-4xl max-h-[85vh] rounded-md overflow-hidden border border-gray-200 flex flex-col bg-white dark:bg-gray-800 dark:border-gray-700"
       
      >
        <div className="flex flex-col overflow-hidden flex-1">
          <div 
            className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700"
          >
            <div>
              <h2 className={textStyles.title}>
                Filtros Avançados
              </h2>
              <p className={`${textStyles.description} mt-0.5`}>
                Refine sua busca com filtros compatíveis com a Base Global
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                {onSave && (
                  <Popover open={isDestinationOpen} onOpenChange={setIsDestinationOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 border-gray-500 text-gray-700 dark:text-gray-300"
                      >
                        <Save className="w-4 h-4" />
                        Salvar
                        <ChevronDown className="w-3 h-3" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent align="end" className="w-72 p-2 bg-white border border-gray-200 dark:border-gray-700">
                      <div className="space-y-1">
                        <p className="text-xs font-medium px-2 py-1.5 text-gray-600">
                          Salvar busca em:
                        </p>
                        {saveDestinations.map((dest) => (
                          <button
                            key={dest.key}
                            onClick={() => {
                              setSaveDestination(dest.key)
                              setIsDestinationOpen(false)
                              onSave(filters, dest.key)
                            }}
                            className={cn(
                              "w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-left transition-colors",
                              saveDestination === dest.key 
                                ? "bg-gray-100" 
                                : "hover:bg-gray-50"
                            )}
                          >
                            <dest.icon 
                              className={cn(
                                "w-4 h-4 flex-shrink-0",
                                saveDestination === dest.key ? "text-gray-800 dark:text-gray-200" : "text-gray-500"
                              )}
                            />
                            <div className="flex-1 min-w-0">
                              <div 
                                className={cn(
                                  "text-xs font-medium",
                                  saveDestination === dest.key ? "text-gray-800" : "text-gray-800"
                                )}
                              >
                                {dest.label}
                              </div>
                              <div className="text-xs text-gray-600">
                                {dest.description}
                              </div>
                            </div>
                            {saveDestination === dest.key && (
                              <Check className="w-4 h-4 flex-shrink-0 text-gray-700 dark:text-gray-300" />
                            )}
                          </button>
                        ))}
                      </div>
                    </PopoverContent>
                  </Popover>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Main Content Area with Sidebar and Scrollable Content */}
          <div className="flex flex-1 overflow-hidden">
            {/* Left Sidebar Menu */}
            <div className="w-sidebar-content flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 overflow-y-auto">
              <nav className="py-3">
                {sidebarCategories.map((category) => {
                  const Icon = category.icon
                  const isActive = activeSection === category.key
                  return (
                    <button
                      key={category.key}
                      onClick={() => scrollToSection(category.key)}
                      className={cn(
                        "w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-xs transition-all",
                        isActive
 ? "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-r-2 border-gray-900 dark:border-gray-700 font-medium"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-800"
                      )}
                    >
                      <Icon className={cn("w-4 h-4", isActive ? "text-gray-900 dark:text-gray-100" : "text-gray-400")} />
                      <span className="truncate">{category.label}</span>
                    </button>
                  )
                })}
              </nav>
            </div>

            {/* Scrollable Filter Sections */}
            <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-6 space-y-8">
              {/* Section: Origem da Busca */}
              <div ref={(el) => { sectionRefs.current.searchSource = el }}>
                <SectionHeader icon={Search} title="Origem da Busca" description="Selecione de onde buscar candidatos" />
                
                <RadioGroup 
                  value={searchSource} 
                  onValueChange={(value) => setSearchSource(value as SearchSource)}
                  className="grid grid-cols-3 gap-3"
                >
                  <label 
                    className={cn(
                      "relative flex flex-col p-4 rounded-md border-2 cursor-pointer transition-all bg-white",
                      searchSource === "local" 
                        ? "border-gray-300 bg-gray-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <RadioGroupItem value="local" id="local" className="sr-only" />
                      <Home className={cn("w-4 h-4", searchSource === "local" ? "text-gray-800 dark:text-gray-200" : "text-gray-500")} />
                      <span 
                        className={cn("font-medium text-xs", searchSource === "local" ? "text-gray-800" : "text-gray-800")}
                      >
                        Base Local
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Candidatos já cadastrados na sua base
                    </p>
                    {searchSource === "local" && (
                      <div 
                        className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-gray-900 dark:bg-gray-100"
                      >
                        <Check className="w-3 h-3 text-white dark:text-gray-900" />
                      </div>
                    )}
                  </label>

                  <label 
                    className={cn(
                      "relative flex flex-col p-4 pt-8 rounded-md border-2 cursor-pointer transition-all bg-white",
                      searchSource === "hybrid" 
                        ? "border-gray-300 bg-gray-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    <Badge 
                      className="absolute top-2 right-2 text-micro px-1.5 py-0.5 font-medium"
                      style={{backgroundColor: "var(--gray-100)", color: "var(--status-warning)", border: "none"}}
                    >
                      1 CRÉDITO/CAND.
                    </Badge>
                    <div className="flex items-center gap-2 mb-2">
                      <RadioGroupItem value="hybrid" id="hybrid" className="sr-only" />
                      <RefreshCw className={cn("w-4 h-4", searchSource === "hybrid" ? "text-gray-800 dark:text-gray-200" : "text-gray-500")} />
                      <span 
                        className={cn("font-medium text-xs", searchSource === "hybrid" ? "text-gray-800" : "text-gray-800")}
                      >
                        Busca Híbrida
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Primeiro local, depois expande para global
                    </p>
                    {searchSource === "hybrid" && (
                      <div 
                        className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-gray-900 dark:bg-gray-100"
                      >
                        <Check className="w-3 h-3 text-white dark:text-gray-900" />
                      </div>
                    )}
                  </label>

                  <label 
                    className={cn(
                      "relative flex flex-col p-4 pt-8 rounded-md border-2 cursor-pointer transition-all bg-white",
                      searchSource === "global" 
                        ? "border-gray-300 bg-gray-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    <Badge 
                      className="absolute top-2 right-2 text-micro px-1.5 py-0.5 font-medium"
                      style={{backgroundColor: "var(--gray-100)", color: "var(--status-warning)", border: "none"}}
                    >
                      1 CRÉDITO/CAND.
                    </Badge>
                    <div className="flex items-center gap-2 mb-2">
                      <RadioGroupItem value="global" id="global" className="sr-only" />
                      <Globe className={cn("w-4 h-4", searchSource === "global" ? "text-gray-800 dark:text-gray-200" : "text-gray-500")} />
                      <span 
                        className={cn("font-medium text-xs", searchSource === "global" ? "text-gray-800" : "text-gray-800")}
                      >
                        Busca Global
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Acesso a +800M de perfis profissionais
                    </p>
                    {searchSource === "global" && (
                      <div 
                        className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-gray-900 dark:bg-gray-100"
                      >
                        <Check className="w-3 h-3 text-white dark:text-gray-900" />
                      </div>
                    )}
                  </label>
                </RadioGroup>

                {(searchSource === "local" || searchSource === "hybrid") && (
                  <div className="mt-4 flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700 bg-white">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-status-warning" />
                      <div>
                        <span className={textStyles.subtitle}>
                          Incluir candidatos descobertos
                        </span>
                        <p className={textStyles.description}>
                          Mostrar candidatos encontrados em buscas anteriores ainda não salvos na base
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={filters.searchOptions?.includeDiscovered ?? true}
                      onCheckedChange={(checked: boolean) => updateFilter("searchOptions", "includeDiscovered", checked)}
                      className="data-[state=checked]:bg-gray-900 dark:data-[state=checked]:bg-gray-100"
                    />
                  </div>
                )}
              </div>
              {/* Section: Opções de Busca */}
              <div ref={(el) => { sectionRefs.current.ppiOptions = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Zap} title="Opções de Busca" description="Controle de qualidade e custo" />
              <div className="space-y-6">
                {(searchSource === "global" || searchSource === "hybrid") && (
                <div 
                  className="p-4 rounded-md border bg-gray-50 border-gray-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Zap className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                      <span className="font-medium text-xs">Custo Estimado</span>
                    </div>
                    <Badge variant="outline" className="text-xs px-1.5 py-0.5 border-gray-500 text-gray-700 dark:text-gray-300">
                      Tempo Real
                    </Badge>
                  </div>
                  
                  <div className="flex items-end justify-between">
                    <div>
                      <div className="text-base font-bold text-gray-900 dark:text-gray-100">
                        {creditEstimate.cost_per_candidate}
                      </div>
                      <div className="text-xs text-gray-600">
                        créditos por candidato
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={textStyles.title}>
                        {creditEstimate.total_estimated}
                      </div>
                      <div className="text-xs text-gray-600">
                        total ({creditEstimate.limit} candidatos)
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-wedo-cyan/20 space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-600">
                        Base ({creditEstimate.pearch_type === "fast" ? "Rápida" : "Profissional"})
                      </span>
                      <span className="font-medium">{creditEstimate.base_cost}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-600">Insights + Scoring</span>
                      <span className="font-medium">+{creditEstimate.insights_cost}</span>
                    </div>
                    {creditEstimate.freshness_cost > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">Dados Atualizados</span>
                        <span className="font-medium">+{creditEstimate.freshness_cost}</span>
                      </div>
                    )}
                    {creditEstimate.email_cost > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">Opções de Email</span>
                        <span className="font-medium">+{creditEstimate.email_cost}</span>
                      </div>
                    )}
                    {creditEstimate.phone_cost > 0 && (
                      <div className="flex justify-between text-xs text-status-warning">
                        <span className="flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          Opções de Telefone
                        </span>
                        <span className="font-medium">+{creditEstimate.phone_cost}</span>
                      </div>
                    )}
                    
                    <div className="flex justify-between text-xs pt-1.5 border-t border-wedo-cyan/15">
                      <span className="flex items-center gap-1 font-medium text-gray-800">
                        <TrendingUp className="w-3 h-3" />
                        Total por Candidato
                      </span>
                      <span className="font-bold text-gray-900 dark:text-gray-100">
                        {creditEstimate.cost_per_candidate}
                      </span>
                    </div>
                  </div>

                  {creditEstimate.warnings.length > 0 && (
                    <div className="mt-3 p-2 bg-status-warning/10 rounded-md border border-status-warning/30">
                      {creditEstimate.warnings.map((warning, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-status-warning">
                          <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          <span>{warning}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                )}

                <div className="space-y-3">
                  <Label className="text-xs font-medium block">Informações de Contato</Label>

                  <div className="flex items-center justify-between p-2.5 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-gray-500" />
                      <div>
                        <div className="text-xs font-medium">Apenas com Email</div>
                        <div className="text-xs text-gray-600">
                          Filtrar candidatos com email
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.requireEmails || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "requireEmails", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                      <div>
                        <div className="text-xs font-medium">Mostrar Emails</div>
                        <div className="text-xs text-gray-600">
                          Exibir emails nos resultados
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.showEmails || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "showEmails", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                      <Phone className="w-4 h-4 text-gray-500" />
                      <div>
                        <div className="text-xs font-medium">Apenas com Telefone</div>
                        <div className="text-xs text-gray-600">
                          Filtrar candidatos com telefone
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.requirePhoneNumbers || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "requirePhoneNumbers", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                      <Phone className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <div>
                        <div className="text-xs font-medium">Mostrar Telefones</div>
                        <div className="text-xs text-gray-600">
                          Exibir telefones nos resultados
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.showPhoneNumbers || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "showPhoneNumbers", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                      <Mail className="w-4 h-4 text-gray-500" />
                      <Phone className="w-4 h-4 -ml-2 text-gray-500" />
                      <div>
                        <div className="text-xs font-medium">Email OU Telefone</div>
                        <div className="text-xs text-gray-500">
                          Pelo menos um contato
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.requirePhonesOrEmails || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "requirePhonesOrEmails", checked)}
                    />
                  </div>
                </div>
              </div>
            </div>

              {/* Section: Geral */}
              <div ref={(el) => { sectionRefs.current.general = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Settings} title="Geral" description="Experiência e perfis" />
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs mb-1.5 block">Experiência Mínima (Anos)</Label>
                    <Input
                      type="number"
                      min={0}
                      value={filters.general?.minExperience || ""}
                      onChange={(e) => updateFilter("general", "minExperience", e.target.value ? parseInt(e.target.value) : undefined)}
                      placeholder="Ex: 3 anos"
                      className="border border-gray-200 focus:ring-1 focus:ring-gray-400"
                    />
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block">Experiência Máxima (Anos)</Label>
                    <Input
                      type="number"
                      min={0}
                      value={filters.general?.maxExperience || ""}
                      onChange={(e) => updateFilter("general", "maxExperience", e.target.value ? parseInt(e.target.value) : undefined)}
                      placeholder="Ex: 10 anos"
                      className="border border-gray-200 focus:ring-1 focus:ring-gray-400"
                    />
                  </div>
                </div>

                <div className="space-y-4 p-4 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50/50">
                  <div className="flex items-center gap-2 mb-3">
                    <Eye className="w-4 h-4 text-gray-600" />
                    <span className={textStyles.subtitle}>
                      Ocultar Perfis Visualizados ou Shortlistados
                    </span>
                    <Popover>
                      <PopoverTrigger asChild>
                        <button 
                          type="button"
                          className="text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <HelpCircle className="w-4 h-4" />
                        </button>
                      </PopoverTrigger>
                      <PopoverContent className="w-80 p-3 bg-white border border-gray-200" side="top">
                        <div className="space-y-2">
                          <h4 className="font-semibold text-sm text-gray-800">O que significa "Shortlistado"?</h4>
                          <p className="text-xs text-gray-600 leading-relaxed">
                            Candidatos <strong>shortlistados</strong> são aqueles que já foram incluídos em vagas e passaram por algum processo de entrevista, seja por você, outros recrutadores ou gestores da organização.
                          </p>
                          <p className="text-xs text-gray-500 leading-relaxed">
                            Isso inclui entrevistas técnicas, comportamentais, com gestores, ou qualquer outra etapa de seleção registrada no sistema.
                          </p>
                        </div>
                      </PopoverContent>
                    </Popover>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs mb-1.5 block text-gray-600">Escopo</Label>
                      <Select
                        value={filters.general?.hideViewedScope || "dont_hide"}
                        onValueChange={(value) => {
                          updateFilter("general", "hideViewedScope", value as HideViewedScope)
                          updateFilter("general", "hideViewedProfiles", value !== "dont_hide")
                        }}
                      >
                        <SelectTrigger className="border border-gray-200 focus:ring-1 focus:ring-gray-400 bg-white text-xs">
                          <SelectValue placeholder="Selecione o escopo" />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          {hideViewedScopeOptions.map(option => (
                            <SelectItem 
                              key={option.value} 
                              value={option.value}
                              className="py-2"
                            >
                              <div>
                                <div className="font-medium">{option.label}</div>
                                {option.description && (
                                  <div className="text-xs text-gray-500">{option.description}</div>
                                )}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label className="text-xs mb-1.5 block text-gray-600">Período</Label>
                      <Select
                        value={filters.general?.hideViewedPeriod || "all_time"}
                        onValueChange={(value) => updateFilter("general", "hideViewedPeriod", value as HideViewedPeriod)}
                        disabled={filters.general?.hideViewedScope === "dont_hide"}
                      >
                        <SelectTrigger 
                          className={cn(
                            "border border-gray-200 focus:ring-1 focus:ring-gray-400 bg-white text-xs",
                            filters.general?.hideViewedScope === "dont_hide" && "opacity-50 cursor-not-allowed"
                          )}
                        >
                          <SelectValue placeholder="Selecione o período" />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          {hideViewedPeriodOptions.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 flex items-center gap-1.5">
                    <AlertCircle className="w-3 h-3" />
                    Remove dos resultados candidatos visualizados ou entrevistados no período selecionado
                  </p>
                </div>
              </div>
            </div>

              {/* Section: Perfil Profissional */}
              <div ref={(el) => { sectionRefs.current.profile = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={UserCheck} title="Perfil Profissional" description="Indicadores de perfil" />
              <div className="space-y-3">
                {isLocalSearch && (
                  <div className="flex items-center gap-2 p-2.5 rounded-md bg-status-warning/10 border border-status-warning/30 mb-3">
                    <Info className="w-4 h-4 text-status-warning flex-shrink-0" />
                    <p className="text-xs text-status-warning">
                      Estes filtros estão disponíveis apenas em busca Híbrida ou Global
                    </p>
                  </div>
                )}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <Briefcase className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-status-success")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Aberto a Oportunidades</div>
                            <div className="text-xs text-gray-500">
                              Candidatos sinalizando interesse em novas propostas
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.ppiOptions?.openToWorkOnly || false}
                          onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "openToWorkOnly", checked)}
                          disabled={isLocalSearch}
                        />
                      </div>
                    </TooltipTrigger>
                    {isLocalSearch && (
                      <TooltipContent side="top">
                        <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                      </TooltipContent>
                    )}
                  </Tooltip>
                </TooltipProvider>
                
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <Crown className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-status-warning")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Decisor / Líder</div>
                            <div className="text-xs text-gray-500">
                              Profissionais em posições de liderança
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.profile?.isDecisionMaker || false}
                          onCheckedChange={(checked: boolean) => updateFilter("profile", "isDecisionMaker", checked)}
                          disabled={isLocalSearch}
                        />
                      </div>
                    </TooltipTrigger>
                    {isLocalSearch && (
                      <TooltipContent side="top">
                        <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                      </TooltipContent>
                    )}
                  </Tooltip>
                </TooltipProvider>
                
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <GraduationCap className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-gray-600 dark:text-gray-400")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Top Universidades</div>
                            <div className="text-xs text-gray-500">
                              Formados em universidades de elite
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.profile?.isTopUniversities || false}
                          onCheckedChange={(checked: boolean) => updateFilter("profile", "isTopUniversities", checked)}
                          disabled={isLocalSearch}
                        />
                      </div>
                    </TooltipTrigger>
                    {isLocalSearch && (
                      <TooltipContent side="top">
                        <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                      </TooltipContent>
                    )}
                  </Tooltip>
                </TooltipProvider>
                
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <Rocket className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-wedo-purple")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Experiência em Startup</div>
                            <div className="text-xs text-gray-500">
                              Trabalhou em startups (cultura ágil)
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.profile?.isStartup || false}
                          onCheckedChange={(checked: boolean) => updateFilter("profile", "isStartup", checked)}
                          disabled={isLocalSearch}
                        />
                      </div>
                    </TooltipTrigger>
                    {isLocalSearch && (
                      <TooltipContent side="top">
                        <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                      </TooltipContent>
                    )}
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>

              {/* Section: Cargo */}
              <div ref={(el) => { sectionRefs.current.job = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Briefcase} title="Cargo" description="Títulos e níveis" />
              <JobFiltersSection 
                filters={filters}
                updateFilter={updateFilter}
                addToArray={addToArray}
                removeFromArray={removeFromArray}
              />
            </div>

              {/* Section: Empresa */}
              <div ref={(el) => { sectionRefs.current.company = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Building2} title="Empresa" description="Empresas e setores" />
              <div className="space-y-6">
                <div>
                  <Label className="text-xs mb-2 block">Empresas</Label>
                  <CompanyFilterInput
                    value={filters.company?.companyItems || []}
                    onChange={(companyItems) => setFilters(prev => ({
                      ...prev,
                      company: {
                        ...(prev.company ?? {}),
                        companyItems
                      }
                    }))}
                    timeFilter={filters.company?.companyTimeFilter || 'current_past'}
                    onTimeFilterChange={(companyTimeFilter) => updateFilter("company", "companyTimeFilter", companyTimeFilter)}
                    specificYears={filters.company?.specificYears}
                    onSpecificYearsChange={(specificYears) => updateFilter("company", "specificYears", specificYears)}
                    fundingStages={filters.company?.fundingStages}
                    onFundingStagesChange={(fundingStages) => updateFilter("company", "fundingStages", fundingStages)}
                    placeholder="Digite empresa e pressione Enter (ex: Google, Microsoft, Nubank)"
                  />
                  <p className="text-xs mt-2 text-gray-500">
                    Dica: Use "Ask AI" para buscar empresas similares ou por descrição (ex: "fintechs em São Paulo")
                  </p>
                </div>

                <div>
                  <Label className="text-xs mb-2 block">Empresas Excluídas</Label>
                  <ExcludedCompaniesInput
                    value={filters.company?.excludedCompanyItems || []}
                    onChange={(excludedCompanyItems) => setFilters(prev => ({
                      ...prev,
                      company: {
                        ...(prev.company ?? {}),
                        excludedCompanyItems
                      }
                    }))}
                    timeFilter={filters.company?.excludedTimeFilter || 'current_only'}
                    onTimeFilterChange={(excludedTimeFilter) => updateFilter("company", "excludedTimeFilter", excludedTimeFilter)}
                    placeholder="Empresas para NÃO incluir nos resultados"
                  />
                  <p className="text-xs mt-1 text-status-warning">
                    Filtro aplicado localmente após Busca Global
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Setores da Empresa</Label>
                    <IndustryFilterInput
                      value={filters.company?.industries || []}
                      onChange={(industries) => setFilters(prev => ({
                        ...prev,
                        company: {
                          ...(prev.company ?? {}),
                          industries
                        }
                      }))}
                      timeFilter={filters.company?.industryTimeFilter || 'current_past'}
                      onTimeFilterChange={(industryTimeFilter) => updateFilter("company", "industryTimeFilter", industryTimeFilter)}
                      placeholder="Digite setor e pressione Enter"
                    />
                  </div>

                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Tags da Empresa</Label>
                    <CompanyTagsInput
                      value={filters.company?.companyTags || []}
                      onChange={(companyTags) => setFilters(prev => ({
                        ...prev,
                        company: {
                          ...(prev.company ?? {}),
                          companyTags
                        }
                      }))}
                      timeFilter={filters.company?.companyTagsTimeFilter || 'current_past'}
                      onTimeFilterChange={(companyTagsTimeFilter) => updateFilter("company", "companyTagsTimeFilter", companyTagsTimeFilter)}
                      placeholder="Digite tag e pressione Enter"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
                            Sede da Empresa
                            {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                          </Label>
                          <CompanyHQLocationsInput
                            value={filters.company?.companyHQLocations || []}
                            disabled={isLocalSearch}
                            onChange={(companyHQLocations) => {
                              if (isLocalSearch) return
                              setFilters(prev => ({
                                ...prev,
                                company: {
                                  ...(prev.company ?? {}),
                                  companyHQLocations
                                }
                              }))
                            }}
                            timeFilter={filters.company?.companyHQTimeFilter || 'current_past'}
                            onTimeFilterChange={(companyHQTimeFilter) => updateFilter("company", "companyHQTimeFilter", companyHQTimeFilter)}
                            placeholder="Ex: São Paulo / Brasil / RJ / ..."
                          />
                        </div>
                      </TooltipTrigger>
                      {isLocalSearch && (
                        <TooltipContent side="top">
                          <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </TooltipProvider>

                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
                            Porte da Empresa
                            {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                          </Label>
                          <div className={cn("flex flex-wrap gap-2", isLocalSearch && "pointer-events-none")}>
                            {companySizes.map(size => {
                              const isSelected = filters.company?.companySizes?.includes(size.value)
                              return (
                                <button
                                  key={size.value}
                                  disabled={isLocalSearch}
                                  onClick={() => {
                                    if (isLocalSearch) return
                                    if (isSelected) {
                                      removeFromArray("company", "companySizes", size.value)
                                    } else {
                                      addToArray("company", "companySizes", size.value)
                                    }
                                  }}
                                  className={cn(
                                    "px-3 py-1.5 rounded-full text-xs border transition-all",
                                    isLocalSearch
                                      ? "border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed"
                                      : isSelected 
                                        ? "border-gray-500 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100" 
                                        : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"
                                  )}
                                >
                                  {size.label}
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      </TooltipTrigger>
                      {isLocalSearch && (
                        <TooltipContent side="top">
                          <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </TooltipProvider>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
                            Empresa Fundada Após
                            {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                          </Label>
                          <div className="relative">
                            <Input
                              type="number"
                              min={1800}
                              max={new Date().getFullYear()}
                              value={filters.company?.companyFoundedAfter || ""}
                              disabled={isLocalSearch}
                              onChange={(e) => {
                                if (isLocalSearch) return
                                const year = e.target.value ? parseInt(e.target.value) : undefined
                                updateFilter("company", "companyFoundedAfter", year)
                              }}
                              placeholder="Ano de Fundação"
                              className={cn(
                                "border-gray-200 focus:ring-1 focus:ring-gray-400 focus:border-gray-500 pr-10",
                                isLocalSearch && "bg-gray-100 cursor-not-allowed"
                              )}
                            />
                            <div className={cn("absolute right-3 top-1/2 transform -translate-y-1/2", isLocalSearch ? "text-gray-300" : "text-gray-400")}>
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                          </div>
                          <p className={cn("text-xs mt-1", isLocalSearch ? "text-gray-400" : "text-gray-500")}>
                            Filtrar empresas fundadas após este ano
                          </p>
                        </div>
                      </TooltipTrigger>
                      {isLocalSearch && (
                        <TooltipContent side="top">
                          <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </TooltipProvider>

                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
                            Estágio de Funding
                            {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                          </Label>
                          <FundingStagesInput
                            value={filters.company?.fundingStages || []}
                            disabled={isLocalSearch}
                            onChange={(fundingStages) => {
                              if (isLocalSearch) return
                              setFilters(prev => ({
                                ...prev,
                                company: {
                                  ...(prev.company ?? {}),
                                  fundingStages
                                }
                              }))
                            }}
                          />
                        </div>
                      </TooltipTrigger>
                      {isLocalSearch && (
                        <TooltipContent side="top">
                          <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>
            </div>

              {/* Section: Habilidades */}
              <div ref={(el) => { sectionRefs.current.skills = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Code} title="Habilidades" description="Skills técnicas" />
              <div className="space-y-6">
                <div>
                  <Label className="text-xs mb-1.5 block">Habilidades Técnicas</Label>
                  <SkillsFilterInput
                    value={filters.skills?.skillItems || []}
                    onChange={(skillItems) => setFilters(prev => ({
                      ...prev,
                      skills: {
                        ...(prev.skills ?? {}),
                        skillItems
                      }
                    }))}
                    placeholder="Digite skill e pressione Enter (ex: Python, React, AWS, SQL)"
                  />
                  <p className="text-xs mt-2 text-gray-500">
                    Dica: Use o ícone de pin para marcar skills obrigatórias. O botão "Find Similar" sugere skills relacionadas via IA.
                  </p>
                </div>

                <div className="mt-4">
                  <Label className="text-xs mb-1.5 block">Áreas de Expertise</Label>
                  <ExpertiseAreasInput
                    value={filters.skills?.expertise || []}
                    onChange={(expertise) => setFilters(prev => ({
                      ...prev,
                      skills: {
                        ...(prev.skills ?? {}),
                        expertise
                      }
                    }))}
                    placeholder="Digite expertise e pressione Enter (ex: Machine Learning, DevOps, Data Science)"
                  />
                </div>
              </div>
            </div>

              {/* Section: Formação */}
              <div ref={(el) => { sectionRefs.current.education = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={GraduationCap} title="Formação" description="Universidades e cursos" />
              <div className="space-y-6">
                <div>
                  <Label className="text-xs mb-2 block font-medium">Universidades</Label>
                  <UniversitiesFilterInput
                    value={filters.education?.universities || []}
                    onChange={(universities) => setFilters(prev => ({
                      ...prev,
                      education: {
                        ...(prev.education ?? {}),
                        universities
                      }
                    }))}
                    placeholder="Digite universidade e pressione Enter"
                    showPresets={true}
                  />
                  <p className="text-xs mt-2 text-gray-500">
                    Dica: Use "Ask AI" para buscar universidades similares ou por descrição
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Universidades Excluídas</Label>
                    <ExcludedUniversitiesInput
                      value={filters.education?.excludedUniversities || []}
                      onChange={(excludedUniversities) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          excludedUniversities
                        }
                      }))}
                      placeholder="USP, UNICAMP, PUC, FGV, etc."
                    />
                  </div>

                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Localização da Universidade</Label>
                    <UniversityLocationsInput
                      value={filters.education?.universityLocations || []}
                      onChange={(universityLocations) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          universityLocations
                        }
                      }))}
                      placeholder="São Paulo / Brasil / RJ / ..."
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Grau Acadêmico</Label>
                    <DegreeRequirementsInput
                      mode={filters.education?.degreeRequirementMode || 'regular'}
                      onModeChange={(degreeRequirementMode) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          degreeRequirementMode
                        }
                      }))}
                      value={filters.education?.degree || null}
                      onChange={(degree) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          degree
                        }
                      }))}
                    />
                  </div>

                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Áreas de Estudo</Label>
                    <FieldsOfStudyInput
                      mode={filters.education?.fieldsOfStudyMode || 'regular'}
                      onModeChange={(fieldsOfStudyMode) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          fieldsOfStudyMode
                        }
                      }))}
                      value={filters.education?.fieldsOfStudy || []}
                      onChange={(fieldsOfStudy) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          fieldsOfStudy
                        }
                      }))}
                      placeholder="Engenharias, Ciências, Computação, etc."
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs mb-1.5 block font-medium">Ano de Formatura</Label>
                  <GraduationYearInput
                    minYear={filters.education?.graduationYearMin ?? null}
                    maxYear={filters.education?.graduationYearMax ?? null}
                    onMinYearChange={(graduationYearMin) => setFilters(prev => ({
                      ...prev,
                      education: {
                        ...(prev.education ?? {}),
                        graduationYearMin
                      }
                    }))}
                    onMaxYearChange={(graduationYearMax) => setFilters(prev => ({
                      ...prev,
                      education: {
                        ...(prev.education ?? {}),
                        graduationYearMax
                      }
                    }))}
                  />
                </div>
              </div>
            </div>

              {/* Section: Idiomas */}
              <div ref={(el) => { sectionRefs.current.languages = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Globe} title="Idiomas" description="Línguas e proficiência" />
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <Label className="text-xs">Idiomas</Label>
                    <Select
                      value={filters.languages?.proficiencyLevel || "any"}
                      onValueChange={(value) => updateFilter("languages", "proficiencyLevel", value)}
                    >
                      <SelectTrigger className="w-auto h-7 px-2 py-1 text-xs border border-gray-200 focus:ring-1 focus:ring-gray-400 gap-1">
                        <SelectValue placeholder="Qualquer Nível" />
                      </SelectTrigger>
                      <SelectContent>
                        {proficiencyLevels.map(level => (
                          <SelectItem key={level.value} value={level.value} className="text-xs">
                            {level.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <LanguageFilterInput
                    value={filters.languages?.languages || []}
                    onAdd={(val) => addToArray("languages", "languages", val)}
                    onRemove={(val) => removeFromArray("languages", "languages", val)}
                    placeholder="Ex: English, Spanish, Mandarin, etc."
                    showPresets={false}
                  />
                </div>
              </div>
            </div>

          </div>
          </div>

          {/* Active Filters Chips */}
          {getActiveFiltersCount() > 0 && (
            <div className="px-6 py-2 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-micro text-gray-500 font-medium">Filtros ativos:</span>
                {filters.general?.minExperience && (
                  <Badge variant="outline" className="text-micro py-0 h-5 gap-1">
                    Exp. mín: {filters.general.minExperience}a
                    <button onClick={() => updateFilter("general", "minExperience", undefined)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                )}
                {filters.general?.maxExperience && (
                  <Badge variant="outline" className="text-micro py-0 h-5 gap-1">
                    Exp. máx: {filters.general.maxExperience}a
                    <button onClick={() => updateFilter("general", "maxExperience", undefined)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                )}
                {filters.job?.titles?.map(t => (
                  <Badge key={t} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {t}
                    <button onClick={() => removeFromArray("job", "titles", t)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
                {filters.skills?.skillItems?.map(s => (
                  <Badge key={s.name} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {s.name}
                    <button onClick={() => {
                      const items = filters.skills?.skillItems?.filter(i => i.name !== s.name) || []
                      setFilters(prev => ({ ...prev, skills: { ...prev.skills, skillItems: items } }))
                    }} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
                {filters.company?.companyItems?.map(c => (
                  <Badge key={c.name} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {c.name}
                    <button onClick={() => {
                      const items = filters.company?.companyItems?.filter(i => i.name !== c.name) || []
                      setFilters(prev => ({ ...prev, company: { ...prev.company, companyItems: items } }))
                    }} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
                {filters.languages?.languages?.map(l => (
                  <Badge key={l} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {l}
                    <button onClick={() => removeFromArray("languages", "languages", l)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div 
            className="flex items-center justify-between px-6 py-3 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700"
          >
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={resetFilters}
                className="text-xs text-gray-500"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Limpar filtros
              </Button>
              {onSave && (
                <div 
                  className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  {(() => {
                    const dest = saveDestinations.find(d => d.key === saveDestination)
                    const Icon = dest?.icon || Bookmark
                    return (
                      <>
                        <Icon className="w-3 h-3" />
                        <span>Salvará em: {dest?.label}</span>
                      </>
                    )
                  })()}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className={textStyles.description}>
                {getActiveFiltersCount()} filtros ativos
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleApply}
                className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                Aplicar Filtros
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      <CreditConfirmationDialog
        open={showCreditConfirm}
        onOpenChange={setShowCreditConfirm}
        onConfirm={handleConfirmSearch}
        candidateLimit={candidateLimit}
        creditPerCandidate={creditEstimate.cost_per_candidate}
        searchType={searchSource === "hybrid" ? "sourcing" : "general"}
        isLoading={isSearching}
      />
    </div>
  )
}

export default AdvancedFiltersModal

