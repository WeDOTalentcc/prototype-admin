"use client"

import React from "react"
import {
  Settings, MapPin, Briefcase, Building2, Code, GraduationCap,
  Globe, Eye, HelpCircle, FolderOpen, History, Bookmark, Zap, UserCheck
} from "lucide-react"
import type { CompanyItem, CompanyTimeFilter } from "./CompanyFilterInput"
import type { ExcludedCompanyItem, ExcludedTimeFilter } from "./ExcludedCompaniesInput"
import type { IndustryTimeFilter } from "./IndustryFilterInput"
import type { CompanyTagItem, CompanyTagsTimeFilter } from "./CompanyTagsInput"
import type { CompanyHQTimeFilter } from "./CompanyHQLocationsInput"
import type { SkillItem } from "./SkillsFilterInput"

export type SaveDestination = "talent_funnel" | "search_history" | "saved_searches"
export type SearchSource = "local" | "global" | "hybrid"

export const saveDestinations: { 
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
    searchType?: "fast"
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

export type FilterCategory = 
  | "ppiOptions"
  | "general" 
  | "job" 
  | "company" 
  | "skills" 
  | "education" 
  | "languages"
  | "profile"

export const categories: { key: FilterCategory; label: string; icon: React.ElementType; description?: string }[] = [
  { key: "ppiOptions", label: "Opções de Busca", icon: Zap, description: "Controle de qualidade e custo" },
  { key: "general", label: "Geral", icon: Settings, description: "Experiência e perfis" },
  { key: "profile", label: "Perfil Profissional", icon: UserCheck, description: "Indicadores de perfil" },
  { key: "job", label: "Cargo", icon: Briefcase, description: "Títulos e níveis" },
  { key: "company", label: "Empresa", icon: Building2, description: "Empresas e setores" },
  { key: "skills", label: "Habilidades", icon: Code, description: "Skills técnicas" },
  { key: "education", label: "Formação", icon: GraduationCap, description: "Universidades e cursos" },
  { key: "languages", label: "Idiomas", icon: Globe, description: "Línguas e proficiência" },
]

export const experienceLevels = [
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

export const jobRoles = [
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

export const titleScopeOptions = [
  { value: "current_only", label: "Cargo Atual", description: "Pessoas com este cargo atualmente" },
  { value: "current_recent", label: "Atual + Recente", description: "Cargo atual ou nos últimos 2 anos" },
  { value: "current_past", label: "Atual + Histórico", description: "Cargo em qualquer ponto da carreira" }
]

export const timeInRoleOptions = [
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

export const tenureOptions = [
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

export const globalJobPresets = [
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

export const companySizes = [
  { value: "emerging", label: "Emergente (até 50 funcionários)" },
  { value: "small", label: "Pequena (51-200 funcionários)" },
  { value: "mid-sized", label: "Média (201-500 funcionários)" },
  { value: "growing", label: "Em Crescimento (501-1000 funcionários)" },
  { value: "large", label: "Grande (1001-5000 funcionários)" },
  { value: "enterprise", label: "Corporação (5001-10000 funcionários)" },
  { value: "large-enterprise", label: "Grande Corporação (10001+)" }
]

export const degreeTypes = [
  { value: "high-school", label: "Ensino Médio" },
  { value: "associate", label: "Tecnólogo" },
  { value: "bachelor", label: "Graduação" },
  { value: "master", label: "Mestrado" },
  { value: "phd", label: "Doutorado" },
  { value: "mba", label: "MBA" }
]

export const proficiencyLevels = [
  { value: "any", label: "Qualquer nível" },
  { value: "native", label: "Nativo" },
  { value: "fluent", label: "Fluente" },
  { value: "professional", label: "Profissional" },
  { value: "intermediate", label: "Intermediário" },
  { value: "basic", label: "Básico" }
]

export const hideViewedScopeOptions: { value: HideViewedScope; label: string; description?: string; isShortlisted?: boolean }[] = [
  { value: "dont_hide", label: "Não ocultar perfis", description: "Mostrar todos os perfis" },
  { value: "by_you_this_project", label: "Visualizados por você neste projeto", description: "Apenas visualizados por você nesta vaga" },
  { value: "by_you_all_projects", label: "Visualizados por você em todos os projetos", description: "Visualizados por você em qualquer vaga" },
  { value: "shortlisted_by_you", label: "Shortlistados por você", description: "Candidatos que você entrevistou", isShortlisted: true },
  { value: "by_org_this_project", label: "Visualizados pela organização neste projeto", description: "Visualizados por qualquer colega nesta vaga" },
  { value: "by_org_all_projects", label: "Visualizados pela organização em todos os projetos", description: "Visualizados por qualquer colega em qualquer vaga" },
  { value: "shortlisted_org_this_project", label: "Shortlistados pela organização neste projeto", description: "Candidatos entrevistados por qualquer colega nesta vaga", isShortlisted: true },
  { value: "shortlisted_org_all_projects", label: "Shortlistados pela organização em todos os projetos", description: "Candidatos entrevistados por qualquer colega em qualquer vaga", isShortlisted: true },
]

export const hideViewedPeriodOptions: { value: HideViewedPeriod; label: string }[] = [
  { value: "all_time", label: "Todo o período" },
  { value: "last_24h", label: "Últimas 24 horas" },
  { value: "last_2_weeks", label: "Últimas 2 semanas" },
  { value: "last_3_months", label: "Últimos 3 meses" },
  { value: "last_6_months", label: "Últimos 6 meses" },
]

export const SectionHeader = ({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description?: string }) => (
  <div className="flex items-center gap-2 mb-4">
    <Icon className="w-5 h-5 text-lia-text-secondary" />
    <div>
      <h3 className="text-sm font-semibold text-lia-text-primary">{title}</h3>
      {description && <p className="text-xs text-lia-text-secondary">{description}</p>}
    </div>
  </div>
)

