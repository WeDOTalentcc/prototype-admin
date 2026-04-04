/**
 * candidate-transforms.ts — Sprint G4.
 *
 * Transforms CandidateLocal (lia-api backend shape) → Candidate (FE display shape).
 * Extracted from candidates-page.tsx to enable reuse across hooks and components.
 *
 * Portabilidade Vue: funções puras, sem dependência de hooks React.
 */
import { formatBRL } from "@/lib/pricing"
import type { CandidateLocal } from "@/services/lia-api"
import type { Candidate } from "@/components/pages/candidates/types"

// ---------------------------------------------------------------------------
// Salary helpers
// ---------------------------------------------------------------------------

const SALARY_RANGES = {
  junior:     { min: 4000,  max: 7000  },
  pleno:      { min: 8000,  max: 14000 },
  senior:     { min: 15000, max: 25000 },
  specialist: { min: 20000, max: 35000 },
  lead:       { min: 25000, max: 40000 },
}

export function getSalaryByExperience(experience: number, index: number): number {
  let range = SALARY_RANGES.junior
  if (experience >= 10)     range = SALARY_RANGES.lead
  else if (experience >= 7) range = SALARY_RANGES.specialist
  else if (experience >= 4) range = SALARY_RANGES.senior
  else if (experience >= 2) range = SALARY_RANGES.pleno

  const variation = (index * 1234) % (range.max - range.min + 1)
  return range.min + variation
}

// ---------------------------------------------------------------------------
// Work history generator
// ---------------------------------------------------------------------------

type WorkEntry = {
  company: string
  title: string
  position: string
  period: string
  startDate: string
  endDate?: string
  description: string
}

export function generateWorkHistory(candidate: CandidateLocal, experience: number): WorkEntry[] {
  const workHistory: WorkEntry[] = []
  const currentYear = new Date().getFullYear()
  const title = candidate.current_title || 'Profissional'
  const company = candidate.current_company || ''
  const seniority = candidate.seniority_level?.toLowerCase() || ''

  const techCompanies = ['TechCorp Brasil', 'Nubank', 'iFood', 'Mercado Livre', 'Stone', 'PicPay', 'Itaú Digital', 'Bradesco Next', 'Movile', 'VTEX', 'Creditas', 'Loft', 'QuintoAndar', 'Wildlife Studios', 'Loggi']
  const startups = ['Startup XYZ', 'InnovaTech', 'FinTech Solutions', 'DataDriven Co', 'CloudFirst', 'AgileHub', 'ScaleTech', 'GrowthLabs']
  const consultancies = ['Accenture', 'McKinsey Digital', 'BCG Gamma', 'KPMG Tech', 'Deloitte Digital', 'EY Brasil']

  const getDescriptionByTitle = (t: string): string => {
    const lower = t.toLowerCase()
    if (lower.includes('cto') || lower.includes('chief')) return 'Liderança técnica e estratégica, definição de arquitetura e roadmap tecnológico'
    if (lower.includes('head') || lower.includes('diretor')) return 'Gestão de equipes multidisciplinares e entrega de projetos estratégicos'
    if (lower.includes('gerente') || lower.includes('manager')) return 'Coordenação de times, gestão de projetos e processos ágeis'
    if (lower.includes('tech lead') || lower.includes('líder')) return 'Liderança técnica de squad, code reviews e mentoria de desenvolvedores'
    if (lower.includes('senior') || lower.includes('sênior')) return 'Desenvolvimento de soluções complexas e mentoria de desenvolvedores juniores'
    if (lower.includes('arquiteto') || lower.includes('architect')) return 'Definição de arquitetura de sistemas e padrões técnicos'
    if (lower.includes('full stack') || lower.includes('fullstack')) return 'Desenvolvimento end-to-end de aplicações web e APIs'
    if (lower.includes('frontend') || lower.includes('front-end')) return 'Desenvolvimento de interfaces responsivas e experiência do usuário'
    if (lower.includes('backend') || lower.includes('back-end')) return 'Desenvolvimento de APIs RESTful e microsserviços'
    if (lower.includes('devops') || lower.includes('sre')) return 'Automação de infraestrutura, CI/CD e monitoramento'
    if (lower.includes('data') || lower.includes('dados')) return 'Análise de dados, machine learning e pipelines de dados'
    if (lower.includes('product') || lower.includes('produto')) return 'Definição de roadmap, discovery e entrega de valor ao usuário'
    if (lower.includes('design') || lower.includes('ux')) return 'Pesquisa de usuário, prototipagem e design de interfaces'
    return 'Desenvolvimento de software e entrega de soluções técnicas'
  }

  if (company) {
    const startYear = currentYear - Math.min(experience, 3)
    workHistory.push({ company, title, position: title, period: `${startYear} - Atual`, startDate: `${startYear}-01-01`, description: getDescriptionByTitle(title) })
  }

  if (experience >= 3) {
    const prevCompanies = seniority.includes('senior') || seniority.includes('lead') || seniority.includes('specialist') ? techCompanies : startups
    const prevCompany = prevCompanies[Math.floor(Math.random() * prevCompanies.length)]
    const prevTitle = title.replace(/Senior|Sênior|Lead|Principal|Staff/gi, '').trim() || 'Desenvolvedor'
    const endYear = company ? currentYear - Math.min(experience, 3) : currentYear - 1
    const startYear = endYear - Math.min(2, Math.floor(experience / 2))
    workHistory.push({ company: prevCompany, title: prevTitle, position: prevTitle, period: `${startYear} - ${endYear}`, startDate: `${startYear}-01-01`, endDate: `${endYear}-12-01`, description: getDescriptionByTitle(prevTitle) })
  }

  if (experience >= 6) {
    const earlyCompany = consultancies[Math.floor(Math.random() * consultancies.length)]
    const earlyTitle = 'Analista de Sistemas'
    const endYear = currentYear - Math.floor(experience / 2) - 1
    const startYear = endYear - 2
    workHistory.push({ company: earlyCompany, title: earlyTitle, position: earlyTitle, period: `${startYear} - ${endYear}`, startDate: `${startYear}-01-01`, endDate: `${endYear}-12-01`, description: 'Desenvolvimento de software e suporte técnico a clientes enterprise' })
  }

  if (workHistory.length === 0) {
    workHistory.push({ company: 'Empresa Atual', title, position: title, period: `${currentYear - 1} - Atual`, startDate: `${currentYear - 1}-01-01`, description: getDescriptionByTitle(title) })
  }

  return workHistory
}

// ---------------------------------------------------------------------------
// Education generator
// ---------------------------------------------------------------------------

type EducationEntry = {
  school: string
  institution: string
  degree: string
  field_of_study: string
  fieldOfStudy: string
  startDate: string
  endDate: string
}

export function generateEducation(candidate: CandidateLocal, experience: number): EducationEntry[] {
  const education: EducationEntry[] = []
  const currentYear = new Date().getFullYear()
  const title = (candidate.current_title || '').toLowerCase()
  const seniority = (candidate.seniority_level || '').toLowerCase()

  const topUniversities = ['USP', 'UNICAMP', 'UFRJ', 'UFMG', 'UFRGS', 'PUC-Rio', 'PUC-SP', 'Insper', 'FGV', 'ITA', 'IME']
  const otherUniversities = ['Mackenzie', 'FIAP', 'FATEC', 'Unisinos', 'PUCRS', 'UFSCar', 'UFSC', 'UFPR', 'UnB', 'UFBA']
  const mbaSchools = ['Insper', 'FGV', 'USP/FIA', 'Fundação Dom Cabral', 'IBMEC', 'BSP', 'Saint Paul']

  const getFieldByTitle = (t: string): string => {
    if (t.includes('data') || t.includes('dados') || t.includes('machine learning') || t.includes('ai')) return 'Ciência de Dados'
    if (t.includes('frontend') || t.includes('front-end') || t.includes('design') || t.includes('ux')) return 'Design Digital'
    if (t.includes('devops') || t.includes('sre') || t.includes('infra')) return 'Engenharia de Computação'
    if (t.includes('product') || t.includes('produto')) return 'Administração de Empresas'
    if (t.includes('security') || t.includes('segurança')) return 'Segurança da Informação'
    return 'Ciência da Computação'
  }

  const isLeadership = seniority.includes('lead') || seniority.includes('head') || seniority.includes('director') ||
    title.includes('cto') || title.includes('gerente') || title.includes('manager') ||
    title.includes('head') || title.includes('diretor') || experience >= 10

  if (isLeadership && experience >= 8) {
    const mbaSchool = mbaSchools[Math.floor(Math.random() * mbaSchools.length)]
    const endYear = currentYear - Math.floor(experience / 3)
    const startYear = endYear - 2
    education.push({ school: mbaSchool, institution: mbaSchool, degree: 'MBA', field_of_study: 'Gestão de Tecnologia e Inovação', fieldOfStudy: 'Gestão de Tecnologia e Inovação', startDate: `${startYear}-02-01`, endDate: `${endYear}-12-01` })
  }

  const isSenior = seniority.includes('senior') || seniority.includes('specialist') || seniority.includes('lead') || experience >= 5
  const universities = isSenior ? topUniversities : otherUniversities
  const university = universities[Math.floor(Math.random() * universities.length)]
  const field = getFieldByTitle(title)
  const gradEndYear = currentYear - experience - 1
  const gradStartYear = gradEndYear - 4
  education.push({ school: university, institution: university, degree: 'Bacharelado', field_of_study: field, fieldOfStudy: field, startDate: `${gradStartYear}-02-01`, endDate: `${gradEndYear}-12-01` })

  if (isSenior && !isLeadership && experience >= 5) {
    const pgSchool = topUniversities[Math.floor(Math.random() * topUniversities.length)]
    const pgEndYear = currentYear - Math.floor(experience / 2)
    const pgStartYear = pgEndYear - 2
    education.push({ school: pgSchool, institution: pgSchool, degree: 'Pós-Graduação', field_of_study: 'Engenharia de Software', fieldOfStudy: 'Engenharia de Software', startDate: `${pgStartYear}-02-01`, endDate: `${pgEndYear}-12-01` })
  }

  return education
}

// ---------------------------------------------------------------------------
// Main transform: CandidateLocal → Candidate
// ---------------------------------------------------------------------------

export function mapCandidateLocalToCandidate(c: CandidateLocal, index: number): Candidate {
  const experience = c.years_of_experience || ((index % 12) + 1)
  const monthlySalary = c.current_salary || getSalaryByExperience(experience, index)

  const nu = <T>(v: T | null | undefined): T | undefined => v ?? undefined

  return {
    id: c.id,
    candidateId: c.id.substring(0, 5).toUpperCase(),
    name: c.name,
    email: c.email || '',
    secondary_email: nu(c.secondary_email),
    phone: c.phone || '',
    mobile_phone: nu(c.mobile_phone),
    secondary_phone: nu(c.secondary_phone),
    linkedin_url: nu(c.linkedin_url),
    github_url: nu(c.github_url),
    portfolio_url: nu(c.portfolio_url),
    avatar_url: nu(c.avatar_url),

    date_of_birth: nu(c.date_of_birth),
    gender: nu(c.gender),
    nationality: nu(c.nationality),
    marital_status: nu(c.marital_status),
    cpf: nu(c.cpf),

    current_title: nu(c.current_title),
    current_company: c.current_company || '',
    seniority_level: nu(c.seniority_level),
    years_of_experience: experience,
    self_introduction: nu(c.self_introduction),

    technical_skills: c.technical_skills || [],
    soft_skills: c.soft_skills || [],
    languages: (c.languages || {}) as Record<string, string> | undefined,
    certifications: c.certifications || [],
    interests: c.interests || [],

    location_city: nu(c.location_city),
    location_state: nu(c.location_state),
    location_country: nu(c.location_country),
    address_street: nu(c.address_street),
    address_number: nu(c.address_number),
    address_district: nu(c.address_district),
    address_zip: nu(c.address_zip),
    address_complement: nu(c.address_complement),

    is_remote: c.is_remote,
    willing_to_relocate: c.willing_to_relocate,
    mobility: c.mobility,
    work_model_preference: c.work_model_preference,
    contract_type_preference: c.contract_type_preference,

    current_salary: monthlySalary,
    salary_currency: c.salary_currency || 'BRL',
    desired_salary_min: nu(c.desired_salary_min),
    desired_salary_max: nu(c.desired_salary_max),
    salary_expectation_clt: nu(c.salary_expectation_clt),
    salary_expectation_pj: nu(c.salary_expectation_pj),
    salary_expectation_freelance: nu(c.salary_expectation_freelance),

    resume_url: nu(c.resume_url),
    resume_text: nu(c.resume_text),
    cover_letter: nu(c.cover_letter),

    source: c.source,
    ats_source_name: nu(c.ats_source_name),
    ats_candidate_id: nu(c.ats_candidate_id),
    pearch_profile_id: nu(c.pearch_profile_id),

    lia_score: c.lia_score,
    lia_insights: c.lia_insights || {},
    skills_match_percentage: c.skills_match_percentage,

    status: c.status,
    is_active: c.is_active,
    is_blacklisted: c.is_blacklisted,
    blacklist_reason: nu(c.blacklist_reason),

    preferred_contact_method: nu(c.preferred_contact_method),
    best_time_to_contact: nu(c.best_time_to_contact),
    communication_consent: c.communication_consent,

    completed_register: c.completed_register,
    accept_terms: c.accept_terms,

    tags: c.tags || [],
    notes: c.notes,
    additional_data: c.additional_data || {},

    created_at: c.created_at,
    updated_at: c.updated_at,
    last_contacted_at: nu(c.last_contacted_at),
    last_activity_at: nu(c.last_activity_at),

    position: c.current_title || 'Não especificado',
    monthlySalary,
    location: c.location_city || 'Não especificado',
    workModel: (c.work_model_preference as 'remoto' | 'híbrido' | 'presencial') || 'remoto',
    score: c.lia_score || 75,
    currentSalary: `${formatBRL(monthlySalary)}`,
    expectedSalary: c.desired_salary_max
      ? `${formatBRL(c.desired_salary_max)}`
      : `${formatBRL(Math.floor(monthlySalary * 1.2))}`,
    contractType: (c.contract_type_preference?.toUpperCase() || 'CLT') as 'CLT' | 'PJ' | 'Freelancer',
    linkedin: c.linkedin_url || '',
    skills: c.technical_skills || [],
    experience,
    workHistory: generateWorkHistory(c, experience),
    education: generateEducation(c, experience),
    avatar: c.avatar_url,
    liaAnalysis: {
      score: c.lia_score || 75,
      strengths: (c.lia_insights?.strengths as string[] | undefined) || ['Perfil técnico sólido'],
      concerns: (c.lia_insights?.concerns as string[] | undefined) || [],
      recommendation: (c.lia_insights?.recommendation as string | undefined) || 'Avaliar com atenção',
    },
    has_email: Boolean(c.email),
    has_phone: Boolean(c.phone),
    is_opentowork: c.is_opentowork,
    is_decision_maker: c.is_decision_maker,
    is_top_universities: c.is_top_universities,
    is_startup: (c.is_startup || (c.company_info as Record<string, unknown> | undefined)?.is_startup) as boolean | undefined,
    expertise: c.expertise,
    outreach_message: c.outreach_message,
  }
}
