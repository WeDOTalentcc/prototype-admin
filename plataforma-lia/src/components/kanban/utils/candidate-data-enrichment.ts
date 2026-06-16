export const TECH_COMPANIES = [
  'TechCorp Brasil', 'Nubank', 'iFood', 'Mercado Livre', 'Stone', 'PicPay', 
  'Itaú Digital', 'Bradesco Next', 'Movile', 'VTEX', 'Creditas', 'Loft', 
  'QuintoAndar', 'Wildlife Studios', 'Loggi'
]

export const STARTUPS = [
  'Startup XYZ', 'InnovaTech', 'FinTech Solutions', 'DataDriven Co', 
  'CloudFirst', 'AgileHub', 'ScaleTech', 'GrowthLabs'
]

export const CONSULTANCIES = [
  'Accenture', 'McKinsey Digital', 'BCG Gamma', 'KPMG Tech', 
  'Deloitte Digital', 'EY Brasil'
]

export const TOP_UNIVERSITIES = [
  'USP', 'UNICAMP', 'UFRJ', 'UFMG', 'UFRGS', 'PUC-Rio', 
  'PUC-SP', 'Insper', 'FGV', 'ITA', 'IME'
]

export const OTHER_UNIVERSITIES = [
  'Mackenzie', 'FIAP', 'FATEC', 'Unisinos', 'PUCRS', 
  'UFSCar', 'UFSC', 'UFPR', 'UnB', 'UFBA'
]

export const MBA_SCHOOLS = [
  'Insper', 'FGV', 'USP/FIA', 'Fundação Dom Cabral', 
  'IBMEC', 'BSP', 'Saint Paul'
]

export const SALARY_RANGES = {
  junior: { min: 4000, max: 7000 },
  pleno: { min: 8000, max: 14000 },
  senior: { min: 15000, max: 25000 },
  specialist: { min: 20000, max: 35000 },
  lead: { min: 25000, max: 40000 }
}

export function seededRandom(seed: string, index: number = 0): number {
  let hash = 0
  const str = seed + String(index)
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash % 100) / 100
}

export function getSalaryByExperience(experience: number, index: number): number {
  let range = SALARY_RANGES.junior
  if (experience >= 10) range = SALARY_RANGES.lead
  else if (experience >= 7) range = SALARY_RANGES.specialist
  else if (experience >= 4) range = SALARY_RANGES.senior
  else if (experience >= 2) range = SALARY_RANGES.pleno
  
  const variation = (index * 1234) % (range.max - range.min + 1)
  return range.min + variation
}

export interface CandidateForDataGeneration {
  id?: string
  current_title?: string
  current_company?: string
  seniority_level?: string
}

export interface WorkHistoryEntry {
  company: string
  title: string
  position: string
  period: string
  startDate: string
  endDate?: string
  description: string
}

export interface EducationEntry {
  school: string
  institution: string
  degree: string
  field_of_study: string
  fieldOfStudy: string
  startDate: string
  endDate: string
}

function getDescriptionByTitle(title: string): string {
  const lower = title.toLowerCase()
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

function getFieldByTitle(title: string): string {
  const t = title.toLowerCase()
  if (t.includes('data') || t.includes('dados') || t.includes('machine learning') || t.includes('ai')) return 'Ciência de Dados'
  if (t.includes('frontend') || t.includes('front-end') || t.includes('design') || t.includes('ux')) return 'Design Digital'
  if (t.includes('devops') || t.includes('sre') || t.includes('infra')) return 'Engenharia de Computação'
  if (t.includes('product') || t.includes('produto')) return 'Administração de Empresas'
  if (t.includes('security') || t.includes('segurança')) return 'Segurança da Informação'
  return 'Ciência da Computação'
}

export function generateWorkHistory(
  candidate: CandidateForDataGeneration, 
  experience: number
): WorkHistoryEntry[] {
  const workHistory: WorkHistoryEntry[] = []
  
  const currentYear = new Date().getFullYear()
  const title = candidate.current_title || 'Profissional'
  const company = candidate.current_company || ''
  const seniority = candidate.seniority_level?.toLowerCase() || ''
  
  if (company) {
    const startYear = currentYear - Math.min(experience, 3)
    workHistory.push({
      company: company,
      title: title,
      position: title,
      period: `${startYear} - Atual`,
      startDate: `${startYear}-01-01`,
      description: getDescriptionByTitle(title)
    })
  }
  
  if (experience >= 3) {
    const prevCompanies = seniority.includes('senior') || seniority.includes('lead') || seniority.includes('specialist') 
      ? TECH_COMPANIES 
      : STARTUPS
    const prevCompany = prevCompanies[Math.floor(seededRandom(candidate.id || '', 20) * prevCompanies.length)]
    const prevTitle = title.replace(/Senior|Sênior|Lead|Principal|Staff/gi, '').trim() || 'Desenvolvedor'
    const endYear = company ? currentYear - Math.min(experience, 3) : currentYear - 1
    const startYear = endYear - Math.min(2, Math.floor(experience / 2))
    
    workHistory.push({
      company: prevCompany,
      title: prevTitle,
      position: prevTitle,
      period: `${startYear} - ${endYear}`,
      startDate: `${startYear}-01-01`,
      endDate: `${endYear}-12-01`,
      description: getDescriptionByTitle(prevTitle)
    })
  }
  
  if (experience >= 6) {
    const earlyCompany = CONSULTANCIES[Math.floor(seededRandom(candidate.id || '', 21) * CONSULTANCIES.length)]
    const earlyTitle = 'Analista de Sistemas'
    const endYear = currentYear - Math.floor(experience / 2) - 1
    const startYear = endYear - 2
    
    workHistory.push({
      company: earlyCompany,
      title: earlyTitle,
      position: earlyTitle,
      period: `${startYear} - ${endYear}`,
      startDate: `${startYear}-01-01`,
      endDate: `${endYear}-12-01`,
      description: 'Desenvolvimento de software e suporte técnico a clientes enterprise'
    })
  }
  
  if (workHistory.length === 0) {
    workHistory.push({
      company: 'Empresa Atual',
      title: title,
      position: title,
      period: `${currentYear - 1} - Atual`,
      startDate: `${currentYear - 1}-01-01`,
      description: getDescriptionByTitle(title)
    })
  }
  
  return workHistory
}

export function generateEducation(
  candidate: CandidateForDataGeneration, 
  experience: number
): EducationEntry[] {
  const education: EducationEntry[] = []
  
  const currentYear = new Date().getFullYear()
  const title = (candidate.current_title || '').toLowerCase()
  const seniority = (candidate.seniority_level || '').toLowerCase()
  
  const isLeadership = seniority.includes('lead') || seniority.includes('head') || seniority.includes('director') || 
                       title.includes('cto') || title.includes('gerente') || title.includes('manager') ||
                       title.includes('head') || title.includes('diretor') || experience >= 10
  
  if (isLeadership && experience >= 8) {
    const mbaSchool = MBA_SCHOOLS[Math.floor(seededRandom(candidate.id || '', 22) * MBA_SCHOOLS.length)]
    const endYear = currentYear - Math.floor(experience / 3)
    const startYear = endYear - 2
    
    education.push({
      school: mbaSchool,
      institution: mbaSchool,
      degree: 'MBA',
      field_of_study: 'Gestão de Tecnologia e Inovação',
      fieldOfStudy: 'Gestão de Tecnologia e Inovação',
      startDate: `${startYear}-02-01`,
      endDate: `${endYear}-12-01`
    })
  }
  
  const isSenior = seniority.includes('senior') || seniority.includes('specialist') || seniority.includes('lead') || experience >= 5
  const universities = isSenior ? TOP_UNIVERSITIES : OTHER_UNIVERSITIES
  const university = universities[Math.floor(seededRandom(candidate.id || '', 23) * universities.length)]
  const field = getFieldByTitle(title)
  const gradEndYear = currentYear - experience - 1
  const gradStartYear = gradEndYear - 4
  
  education.push({
    school: university,
    institution: university,
    degree: 'Bacharelado',
    field_of_study: field,
    fieldOfStudy: field,
    startDate: `${gradStartYear}-02-01`,
    endDate: `${gradEndYear}-12-01`
  })
  
  if (isSenior && !isLeadership && experience >= 5) {
    const pgSchool = TOP_UNIVERSITIES[Math.floor(seededRandom(candidate.id || '', 24) * TOP_UNIVERSITIES.length)]
    const pgEndYear = currentYear - Math.floor(experience / 2)
    const pgStartYear = pgEndYear - 2
    
    education.push({
      school: pgSchool,
      institution: pgSchool,
      degree: 'Pós-Graduação',
      field_of_study: 'Engenharia de Software',
      fieldOfStudy: 'Engenharia de Software',
      startDate: `${pgStartYear}-02-01`,
      endDate: `${pgEndYear}-12-01`
    })
  }
  
  return education
}
