/**
 * Skill Weight Inference Utilities
 *
 * Extraído de expanded-chat-modal.tsx (Sprint 4.1 — 2026-03-27).
 * Funções puras de inferência de peso de skills baseadas em cargo/área/senioridade.
 * Sem dependências React — compatível com migração Vue.
 */

// Skill/Competency weight inference result
export interface SkillWeightInference {
  weight: number
  justificativa: string
}

// Local skills catalog for competency suggestions (based on backend SkillsCatalogService)
export const SKILLS_CATALOG: Record<string, { technical: string[]; behavioral: string[] }> = {
  'engineering': {
    technical: ['Python', 'Java', 'Node.js', 'React', 'TypeScript', 'SQL', 'Docker', 'AWS', 'Git', 'Linux', 'MongoDB', 'PostgreSQL', 'Kubernetes', 'CI/CD', 'REST API'],
    behavioral: ['Resolução de Problemas', 'Trabalho em Equipe', 'Comunicação', 'Adaptabilidade', 'Pensamento Analítico']
  },
  'finance': {
    technical: ['Excel Avançado', 'Power BI', 'SAP', 'IFRS', 'Contabilidade Geral', 'Conciliação', 'Fechamento Contábil', 'Orçamento', 'Forecast', 'Análise de Variância', 'ERP', 'SPED', 'Compliance Fiscal'],
    behavioral: ['Ética e Integridade', 'Orientação a Resultados', 'Pensamento Analítico', 'Atenção a Detalhes', 'Organização']
  },
  'hr': {
    technical: ['R&S', 'Entrevistas por Competências', 'ATS', 'LinkedIn Recruiter', 'T&D', 'Gestão de Desempenho', 'People Analytics', 'Employer Branding', 'eSocial', 'Folha de Pagamento'],
    behavioral: ['Comunicação', 'Empatia', 'Colaboração', 'Resolução de Conflitos', 'Influência']
  },
  'marketing': {
    technical: ['SEO', 'SEM', 'Google Ads', 'Meta Ads', 'Analytics', 'Copywriting', 'Social Media', 'Inbound Marketing', 'CRM', 'Growth Hacking'],
    behavioral: ['Criatividade', 'Comunicação', 'Adaptabilidade', 'Orientação a Resultados', 'Pensamento Estratégico']
  },
  'sales': {
    technical: ['Vendas Consultivas', 'CRM', 'Salesforce', 'HubSpot', 'Negociação', 'Prospecção', 'Pipeline Management', 'Forecast', 'Account Management', 'Solution Selling'],
    behavioral: ['Comunicação', 'Orientação a Resultados', 'Resiliência', 'Persuasão', 'Foco no Cliente']
  }
}

// Role to area mapping for skill suggestions
export const ROLE_AREA_MAPPING: Record<string, string> = {
  'desenvolvedor': 'engineering', 'developer': 'engineering', 'engenheiro': 'engineering', 'engineer': 'engineering',
  'programador': 'engineering', 'tech lead': 'engineering', 'arquiteto': 'engineering', 'devops': 'engineering',
  'data': 'engineering', 'cientista': 'engineering', 'fullstack': 'engineering', 'frontend': 'engineering', 'backend': 'engineering',
  'analista contábil': 'finance', 'analista fiscal': 'finance', 'analista financeiro': 'finance', 'controller': 'finance',
  'contador': 'finance', 'tesoureiro': 'finance', 'fp&a': 'finance', 'tributário': 'finance', 'controladoria': 'finance',
  'analista de rh': 'hr', 'recrutador': 'hr', 'headhunter': 'hr', 'business partner': 'hr', 'talent': 'hr',
  'dp': 'hr', 'departamento pessoal': 'hr', 'recursos humanos': 'hr', 't&d': 'hr',
  'marketing': 'marketing', 'growth': 'marketing', 'copywriter': 'marketing', 'social media': 'marketing',
  'content': 'marketing', 'seo': 'marketing', 'branding': 'marketing', 'comunicação': 'marketing',
  'vendedor': 'sales', 'vendas': 'sales', 'comercial': 'sales', 'account': 'sales', 'sales': 'sales',
  'executivo de vendas': 'sales', 'key account': 'sales', 'pré-vendas': 'sales', 'sdr': 'sales'
}

// Core skills mapping for different roles
export const CORE_SKILLS_BY_ROLE: Record<string, string[]> = {
  'python': ['Python', 'Django', 'Flask', 'FastAPI', 'Pandas', 'NumPy'],
  'java': ['Java', 'Spring', 'Spring Boot', 'Hibernate', 'Maven', 'Gradle'],
  'javascript': ['JavaScript', 'TypeScript', 'Node.js', 'React', 'Vue', 'Angular'],
  'frontend': ['React', 'Vue', 'Angular', 'TypeScript', 'JavaScript', 'CSS', 'HTML'],
  'backend': ['Node.js', 'Python', 'Java', 'Go', 'SQL', 'REST API', 'GraphQL'],
  'fullstack': ['React', 'Node.js', 'TypeScript', 'SQL', 'REST API', 'Docker'],
  'data': ['Python', 'SQL', 'Pandas', 'Machine Learning', 'Power BI', 'Tableau'],
  'devops': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Terraform', 'Linux', 'Jenkins'],
  'mobile': ['React Native', 'Flutter', 'Swift', 'Kotlin', 'iOS', 'Android'],
  'analista': ['Excel', 'Power BI', 'SQL', 'SAP'],
  'financeiro': ['Excel', 'SAP', 'Power BI', 'IFRS', 'Contabilidade'],
  'rh': ['R&S', 'eSocial', 'People Analytics', 'ATS', 'LinkedIn Recruiter'],
  'marketing': ['Google Ads', 'Meta Ads', 'SEO', 'Analytics', 'CRM'],
  'comercial': ['CRM', 'Salesforce', 'HubSpot', 'Vendas Consultivas', 'Negociação'],
}

const LEADERSHIP_KEYWORDS = ['gerente', 'coordenador', 'diretor', 'head', 'líder', 'lead', 'manager', 'supervisor', 'superintendente', 'vp', 'cto', 'ceo', 'cfo', 'coo']
const COMMERCIAL_KEYWORDS = ['vendedor', 'vendas', 'comercial', 'account', 'sales', 'executivo de vendas', 'key account', 'sdr', 'bdr', 'closer']
const TECHNICAL_KEYWORDS = ['desenvolvedor', 'developer', 'engenheiro', 'engineer', 'programador', 'analista de sistemas', 'arquiteto', 'devops', 'sre', 'cientista', 'data']

const SENIORITY_LEVELS: Record<string, number> = {
  'junior': 1, 'júnior': 1, 'jr': 1, 'trainee': 1, 'estagiário': 1,
  'pleno': 2, 'pl': 2,
  'sênior': 3, 'senior': 3, 'sr': 3,
  'especialista': 4, 'principal': 4, 'staff': 4,
  'diretor': 5, 'gerente': 4, 'coordenador': 3, 'head': 5, 'líder': 3, 'lead': 3
}

export function detectAreaFromRole(role: string): string | null {
  const roleLower = role.toLowerCase()
  for (const [keyword, area] of Object.entries(ROLE_AREA_MAPPING)) {
    if (roleLower.includes(keyword)) return area
  }
  return null
}

export function getSkillSuggestions(role: string | null, area: string | null): { technical: string[]; behavioral: string[] } {
  let detectedArea: string | null = role ? detectAreaFromRole(role) : null

  if (!detectedArea && area) {
    const areaLower = area.toLowerCase()
    if (areaLower.includes('tecnologia') || areaLower.includes('ti') || areaLower.includes('engenharia')) detectedArea = 'engineering'
    else if (areaLower.includes('financeiro') || areaLower.includes('contábil') || areaLower.includes('fiscal')) detectedArea = 'finance'
    else if (areaLower.includes('rh') || areaLower.includes('recursos humanos') || areaLower.includes('people')) detectedArea = 'hr'
    else if (areaLower.includes('marketing') || areaLower.includes('comunicação')) detectedArea = 'marketing'
    else if (areaLower.includes('comercial') || areaLower.includes('vendas') || areaLower.includes('sales')) detectedArea = 'sales'
  }

  if (detectedArea && SKILLS_CATALOG[detectedArea]) return SKILLS_CATALOG[detectedArea]
  return { technical: [], behavioral: [] }
}

export function detectSeniorityLevel(cargo: string, senioridade?: string): number {
  const text = `${cargo} ${senioridade || ''}`.toLowerCase()
  for (const [keyword, level] of Object.entries(SENIORITY_LEVELS)) {
    if (text.includes(keyword)) return level
  }
  return 2
}

export function isLeadershipRole(cargo: string): boolean {
  const cargoLower = cargo.toLowerCase()
  return LEADERSHIP_KEYWORDS.some(kw => cargoLower.includes(kw))
}

export function isCommercialRole(cargo: string): boolean {
  const cargoLower = cargo.toLowerCase()
  return COMMERCIAL_KEYWORDS.some(kw => cargoLower.includes(kw))
}

export function isTechnicalRole(cargo: string): boolean {
  const cargoLower = cargo.toLowerCase()
  return TECHNICAL_KEYWORDS.some(kw => cargoLower.includes(kw))
}

export function getCoreSkillsForRole(cargo: string): string[] {
  const cargoLower = cargo.toLowerCase()
  const coreSkills: string[] = []
  for (const [roleKey, skills] of Object.entries(CORE_SKILLS_BY_ROLE)) {
    if (cargoLower.includes(roleKey)) coreSkills.push(...skills)
  }
  return [...new Set(coreSkills)]
}

export function inferTechnicalSkillWeight(skill: string, cargo: string, senioridade: string, area: string): SkillWeightInference {
  const skillLower = skill.toLowerCase()
  const areaLower = area.toLowerCase()
  const seniorityLevel = detectSeniorityLevel(cargo, senioridade)
  const coreSkills = getCoreSkillsForRole(cargo)

  const isCore = coreSkills.some(cs => cs.toLowerCase() === skillLower || skillLower.includes(cs.toLowerCase()) || cs.toLowerCase().includes(skillLower))
  if (isCore) {
    return {
      weight: Math.min(5, 4 + (seniorityLevel >= 3 ? 1 : 0)),
      justificativa: `${skill} é competência core para ${cargo || 'esta posição'}`
    }
  }

  const areaSkills = SKILLS_CATALOG[areaLower]?.technical || []
  const isAreaRelated = areaSkills.some(as => as.toLowerCase() === skillLower || skillLower.includes(as.toLowerCase()))
  if (isAreaRelated) {
    return {
      weight: seniorityLevel >= 3 ? 4 : 3,
      justificativa: `${skill} é relevante para profissionais da área de ${area || 'tecnologia'}`
    }
  }

  const commonTools = ['git', 'docker', 'linux', 'sql', 'excel', 'power bi', 'jira']
  if (commonTools.some(tool => skillLower.includes(tool))) {
    return { weight: 3, justificativa: `${skill} é ferramenta padrão utilizada no mercado` }
  }

  return { weight: 2, justificativa: `${skill} é competência desejável para complementar o perfil` }
}

export function inferBehavioralSkillWeight(skill: string, cargo: string, senioridade: string, area: string): SkillWeightInference {
  const skillLower = skill.toLowerCase()
  const seniorityLevel = detectSeniorityLevel(cargo, senioridade)

  if (isLeadershipRole(cargo)) {
    if (skillLower.includes('liderança') || skillLower.includes('leadership'))
      return { weight: 5, justificativa: `Liderança é essencial para cargos de Gerente/Coordenador` }
    if (skillLower.includes('comunicação') || skillLower.includes('communication'))
      return { weight: 5, justificativa: `Comunicação é fundamental para gestão de equipes` }
    if (skillLower.includes('gestão de pessoas') || skillLower.includes('people management'))
      return { weight: 5, justificativa: `Gestão de pessoas é competência core para líderes` }
    if (skillLower.includes('visão estratégica') || skillLower.includes('pensamento estratégico'))
      return { weight: 4, justificativa: `Pensamento estratégico é esperado de gestores` }
  }

  if (isCommercialRole(cargo)) {
    if (skillLower.includes('negociação') || skillLower.includes('negotiation'))
      return { weight: 5, justificativa: `Negociação é competência core para área comercial` }
    if (skillLower.includes('persuasão') || skillLower.includes('influência'))
      return { weight: 4, justificativa: `Persuasão é essencial para conversão de vendas` }
    if (skillLower.includes('orientação a resultados') || skillLower.includes('foco em resultados'))
      return { weight: 5, justificativa: `Orientação a resultados é fundamental para atingir metas comerciais` }
    if (skillLower.includes('resiliência'))
      return { weight: 4, justificativa: `Resiliência é importante para lidar com ciclos de vendas` }
  }

  if (isTechnicalRole(cargo)) {
    if (skillLower.includes('resolução de problemas') || skillLower.includes('problem solving'))
      return { weight: 5, justificativa: `Resolução de problemas é competência core para cargos técnicos` }
    if (skillLower.includes('pensamento analítico') || skillLower.includes('analytical'))
      return { weight: 5, justificativa: `Pensamento analítico é essencial para desenvolvimento de software` }
    if (skillLower.includes('aprendizado contínuo') || skillLower.includes('autodesenvolvimento'))
      return { weight: 4, justificativa: `Aprendizado contínuo é crucial na área de tecnologia` }
  }

  if (skillLower.includes('comunicação') || skillLower.includes('communication'))
    return { weight: seniorityLevel >= 3 ? 5 : 4, justificativa: `Comunicação é competência essencial para colaboração em equipe` }
  if (skillLower.includes('trabalho em equipe') || skillLower.includes('colaboração'))
    return { weight: 4, justificativa: `Trabalho em equipe é fundamental para projetos colaborativos` }
  if (skillLower.includes('adaptabilidade') || skillLower.includes('flexibilidade'))
    return { weight: 3, justificativa: `Adaptabilidade é valorizada em ambientes dinâmicos` }
  if (skillLower.includes('proatividade') || skillLower.includes('iniciativa'))
    return { weight: seniorityLevel >= 3 ? 4 : 3, justificativa: `Proatividade é esperada para crescimento profissional` }
  if (skillLower.includes('organização') || skillLower.includes('gestão do tempo'))
    return { weight: 3, justificativa: `Organização contribui para produtividade individual` }

  return { weight: 3, justificativa: `${skill} é competência comportamental relevante para o perfil` }
}

export function inferSkillWeight(
  skill: string,
  cargo: string,
  senioridade: string,
  area: string,
  type: 'technical' | 'behavioral'
): SkillWeightInference {
  return type === 'technical'
    ? inferTechnicalSkillWeight(skill, cargo, senioridade, area)
    : inferBehavioralSkillWeight(skill, cargo, senioridade, area)
}
