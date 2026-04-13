import type { TableColumn, TableCandidate } from "./types"

export const ID_ALIASES: Record<string, string> = {
  role: 'current_title',
  currentCompany: 'current_company',
  candidate: 'name',
  position: 'current_title',
  company: 'current_company',
  score: 'lia_score',
  location: 'location_city',
  linkedin: 'linkedin_url',
  salary: 'desired_salary_max',
}

export interface ColumnCategory {
  id: string
  label: string
  description?: string
}

export const COLUMN_CATEGORIES: ColumnCategory[] = [
  { id: 'basico', label: 'Básico', description: 'Informações básicas do candidato' },
  { id: 'contato', label: 'Contato', description: 'Informações de contato' },
  { id: 'pessoal', label: 'Pessoal', description: 'Dados pessoais' },
  { id: 'profissional', label: 'Profissional', description: 'Informações profissionais' },
  { id: 'competencias', label: 'Competências', description: 'Habilidades e conhecimentos' },
  { id: 'localizacao', label: 'Localização', description: 'Cidade, estado, país' },
  { id: 'endereco', label: 'Endereço', description: 'Endereço completo' },
  { id: 'preferencias', label: 'Preferências', description: 'Preferências de trabalho' },
  { id: 'salario', label: 'Salário', description: 'Informações salariais' },
  { id: 'documentos', label: 'Documentos', description: 'Currículo e documentos' },
  { id: 'origem', label: 'Origem', description: 'Fonte e integração' },
  { id: 'ia', label: 'IA / Match', description: 'Scores e insights da LIA' },
  { id: 'status', label: 'Status', description: 'Status no funil' },
  { id: 'comunicacao', label: 'Comunicação', description: 'Preferências de comunicação' },
  { id: 'cadastro', label: 'Cadastro', description: 'Status de cadastro' },
  { id: 'adicional', label: 'Adicional', description: 'Informações adicionais' },
  { id: 'datas', label: 'Datas', description: 'Timestamps e datas' },
  { id: 'busca_global', label: 'Busca Global', description: 'Dados exclusivos da busca global Pearch' },
]

export interface StandardColumnDefinition extends Omit<TableColumn, 'visible' | 'order'> {
  defaultVisible: boolean
  defaultOrder: number
  category: string
  sortable?: boolean
  width?: number | string
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  isGlobalSearch?: boolean
}

export const ALL_COLUMN_DEFINITIONS: StandardColumnDefinition[] = [
  // ============================================
  // CAMPOS VISÍVEIS POR PADRÃO (11 colunas)
  // ============================================
  { id: 'source', label: 'Fonte', defaultVisible: true, defaultOrder: -1, category: 'basico', width: 60, align: 'center' },
  { id: 'match_score', label: 'Match', defaultVisible: true, defaultOrder: -0.5, category: 'ia', width: 50, align: 'center', sortable: true },
  { id: 'name', label: 'Candidato', defaultVisible: true, defaultOrder: 0, category: 'basico', width: 220, minWidth: 150, sortable: true },
  { id: 'current_title', label: 'Cargo atual', defaultVisible: true, defaultOrder: 1, category: 'profissional', width: 250, minWidth: 120, sortable: true },
  { id: 'current_company', label: 'Empresa atual', defaultVisible: true, defaultOrder: 2, category: 'profissional', width: 150, minWidth: 100, sortable: true },
  { id: 'current_salary', label: 'Salário atual', defaultVisible: true, defaultOrder: 3, category: 'salario', width: 130, sortable: true },
  { id: 'desired_salary_max', label: 'Expectativa salarial', defaultVisible: true, defaultOrder: 4, category: 'salario', width: 130, sortable: true },
  { id: 'mobile_phone', label: 'Celular', defaultVisible: true, defaultOrder: 5, category: 'contato', width: 130 },
  { id: 'email', label: 'E-mail', defaultVisible: true, defaultOrder: 6, category: 'contato', width: 200 },
  { id: 'location_city', label: 'Cidade', defaultVisible: true, defaultOrder: 7, category: 'localizacao', width: 120, sortable: true },
  { id: 'linkedin_url', label: 'LinkedIn', defaultVisible: true, defaultOrder: 8, category: 'contato', width: 60, align: 'center' },

  // ============================================
  // IDENTIFICAÇÃO E CONTATO
  // ============================================
  { id: 'id', label: 'ID do candidato', defaultVisible: false, defaultOrder: 9, category: 'basico', width: 100 },
  { id: 'secondary_email', label: 'E-mail secundário', defaultVisible: false, defaultOrder: 10, category: 'contato', width: 200 },
  { id: 'phone', label: 'Telefone fixo', defaultVisible: false, defaultOrder: 11, category: 'contato', width: 130 },
  { id: 'secondary_phone', label: 'Telefone adicional', defaultVisible: false, defaultOrder: 12, category: 'contato', width: 130 },
  { id: 'github_url', label: 'GitHub', defaultVisible: false, defaultOrder: 13, category: 'contato', width: 150 },
  { id: 'portfolio_url', label: 'Portfólio', defaultVisible: false, defaultOrder: 14, category: 'contato', width: 150 },

  // ============================================
  // INFORMAÇÕES PESSOAIS
  // ============================================
  { id: 'date_of_birth', label: 'Data de nascimento', defaultVisible: false, defaultOrder: 15, category: 'pessoal', width: 120 },
  { id: 'gender', label: 'Gênero', defaultVisible: false, defaultOrder: 17, category: 'pessoal', width: 100 },
  { id: 'nationality', label: 'Nacionalidade', defaultVisible: false, defaultOrder: 18, category: 'pessoal', width: 130 },
  { id: 'marital_status', label: 'Estado civil', defaultVisible: false, defaultOrder: 19, category: 'pessoal', width: 120 },
  { id: 'cpf', label: 'CPF', defaultVisible: false, defaultOrder: 20, category: 'pessoal', width: 130 },

  // ============================================
  // PERFIL PROFISSIONAL
  // ============================================
  { id: 'seniority_level', label: 'Nível de senioridade', defaultVisible: false, defaultOrder: 21, category: 'profissional', width: 130, sortable: true },
  { id: 'years_of_experience', label: 'Anos de experiência', defaultVisible: false, defaultOrder: 22, category: 'profissional', width: 100, sortable: true },
  { id: 'self_introduction', label: 'Autoapresentação', defaultVisible: false, defaultOrder: 23, category: 'profissional', width: 200 },
  { id: 'company_hq', label: 'Sede da Empresa', defaultVisible: false, defaultOrder: 23.1, category: 'profissional', width: 150, sortable: true },
  { id: 'funding_stage', label: 'Estágio de Funding', defaultVisible: false, defaultOrder: 23.2, category: 'profissional', width: 140, sortable: true },
  { id: 'institution_tier', label: 'Tier da Instituição', defaultVisible: false, defaultOrder: 23.3, category: 'profissional', width: 130, sortable: true },
  { id: 'company_industries', label: 'Segmentos da Empresa', defaultVisible: false, defaultOrder: 23.4, category: 'profissional', width: 180 },
  { id: 'company_size', label: 'Tamanho da Empresa', defaultVisible: false, defaultOrder: 23.5, category: 'profissional', width: 140, sortable: true },

  // ============================================
  // COMPETÊNCIAS E HABILIDADES
  // ============================================
  { id: 'technical_skills', label: 'Habilidades técnicas', defaultVisible: false, defaultOrder: 24, category: 'competencias', width: 200 },
  { id: 'soft_skills', label: 'Comp. Comportamentais', defaultVisible: false, defaultOrder: 25, category: 'competencias', width: 180 },
  { id: 'languages', label: 'Idiomas', defaultVisible: false, defaultOrder: 26, category: 'competencias', width: 150 },
  { id: 'certifications', label: 'Certificações', defaultVisible: false, defaultOrder: 27, category: 'competencias', width: 180 },
  { id: 'interests', label: 'Interesses', defaultVisible: false, defaultOrder: 28, category: 'competencias', width: 150 },

  // ============================================
  // LOCALIZAÇÃO - CIDADE/ESTADO/PAÍS
  // ============================================
  { id: 'location_state', label: 'Estado', defaultVisible: false, defaultOrder: 29, category: 'localizacao', width: 100, sortable: true },
  { id: 'location_country', label: 'País', defaultVisible: false, defaultOrder: 30, category: 'localizacao', width: 100, sortable: true },
  { id: 'timezone', label: 'Fuso Horário', defaultVisible: false, defaultOrder: 30.5, category: 'localizacao', width: 140, sortable: true },

  // ============================================
  // ENDEREÇO COMPLETO
  // ============================================
  { id: 'address_street', label: 'Endereço – Rua', defaultVisible: false, defaultOrder: 31, category: 'endereco', width: 180 },
  { id: 'address_number', label: 'Endereço – Número', defaultVisible: false, defaultOrder: 32, category: 'endereco', width: 80 },
  { id: 'address_district', label: 'Endereço – Bairro', defaultVisible: false, defaultOrder: 33, category: 'endereco', width: 120 },
  { id: 'address_zip', label: 'Endereço – CEP', defaultVisible: false, defaultOrder: 34, category: 'endereco', width: 100 },
  { id: 'address_complement', label: 'Endereço – Complemento', defaultVisible: false, defaultOrder: 35, category: 'endereco', width: 150 },

  // ============================================
  // PREFERÊNCIAS DE TRABALHO
  // ============================================
  { id: 'is_remote', label: 'Aceita remoto', defaultVisible: false, defaultOrder: 36, category: 'preferencias', width: 100 },
  { id: 'willing_to_relocate', label: 'Aceita mudança', defaultVisible: false, defaultOrder: 37, category: 'preferencias', width: 100 },
  { id: 'mobility', label: 'Disponibilidade para viagens', defaultVisible: false, defaultOrder: 38, category: 'preferencias', width: 100 },
  { id: 'work_model_preference', label: 'Modelo de trabalho preferido', defaultVisible: false, defaultOrder: 39, category: 'preferencias', width: 130, sortable: true },
  { id: 'contract_type_preference', label: 'Tipo de contrato preferido', defaultVisible: false, defaultOrder: 40, category: 'preferencias', width: 130, sortable: true },

  // ============================================
  // SALÁRIO E EXPECTATIVAS
  // ============================================
  { id: 'salary_currency', label: 'Moeda do salário', defaultVisible: false, defaultOrder: 41, category: 'salario', width: 80 },
  { id: 'desired_salary_min', label: 'Salário mínimo desejado', defaultVisible: false, defaultOrder: 42, category: 'salario', width: 130, sortable: true },
  { id: 'salary_expectation_clt', label: 'Expectativa salarial CLT', defaultVisible: false, defaultOrder: 44, category: 'salario', width: 130, sortable: true },
  { id: 'salary_expectation_pj', label: 'Expectativa salarial PJ', defaultVisible: false, defaultOrder: 45, category: 'salario', width: 130, sortable: true },
  { id: 'salary_expectation_freelance', label: 'Expectativa salarial Freelance', defaultVisible: false, defaultOrder: 46, category: 'salario', width: 130, sortable: true },

  // ============================================
  // CURRÍCULO E DOCUMENTOS
  // ============================================
  { id: 'resume_url', label: 'Currículo (URL)', defaultVisible: false, defaultOrder: 47, category: 'documentos', width: 150 },
  { id: 'resume_text', label: 'Currículo (texto)', defaultVisible: false, defaultOrder: 48, category: 'documentos', width: 200 },
  { id: 'cover_letter', label: 'Carta de apresentação', defaultVisible: false, defaultOrder: 49, category: 'documentos', width: 200 },

  // ============================================
  // ORIGEM E INTEGRAÇÃO
  // ============================================
  { id: 'ats_source_name', label: 'Nome do ATS', defaultVisible: false, defaultOrder: 51, category: 'origem', width: 120 },
  { id: 'ats_candidate_id', label: 'ID no ATS', defaultVisible: false, defaultOrder: 52, category: 'origem', width: 120 },
  { id: 'pearch_profile_id', label: 'ID na Base Global', defaultVisible: false, defaultOrder: 53, category: 'origem', width: 120 },

  // ============================================
  // INSIGHTS LIA / IA
  // ============================================
  { id: 'lia_score', label: 'Score LIA', defaultVisible: false, defaultOrder: 54, category: 'ia', width: 100, sortable: true, align: 'center' },
  { id: 'lia_insights', label: 'Insights LIA', defaultVisible: false, defaultOrder: 55, category: 'ia', width: 200 },
  { id: 'skills_match_percentage', label: '% Match de habilidades', defaultVisible: false, defaultOrder: 56, category: 'ia', width: 100, align: 'center' },

  // ============================================
  // STATUS E WORKFLOW
  // ============================================
  { id: 'status', label: 'Status', defaultVisible: false, defaultOrder: 57, category: 'status', width: 180, sortable: true },
  { id: 'is_active', label: 'Ativo no sistema', defaultVisible: false, defaultOrder: 58, category: 'status', width: 80 },
  { id: 'is_blacklisted', label: 'LCNU', defaultVisible: false, defaultOrder: 59, category: 'status', width: 100 },
  { id: 'blacklist_reason', label: 'Motivo LCNU', defaultVisible: false, defaultOrder: 60, category: 'status', width: 150 },

  // ============================================
  // COMUNICAÇÃO
  // ============================================
  { id: 'preferred_contact_method', label: 'Método de contato preferido', defaultVisible: false, defaultOrder: 61, category: 'comunicacao', width: 130 },
  { id: 'best_time_to_contact', label: 'Melhor horário para contato', defaultVisible: false, defaultOrder: 62, category: 'comunicacao', width: 130 },
  { id: 'communication_consent', label: 'Consentimento LGPD', defaultVisible: false, defaultOrder: 63, category: 'comunicacao', width: 100 },

  // ============================================
  // STATUS DE CADASTRO
  // ============================================
  { id: 'completed_register', label: 'Cadastro completo', defaultVisible: false, defaultOrder: 64, category: 'cadastro', width: 100 },
  { id: 'accept_terms', label: 'Aceite dos termos', defaultVisible: false, defaultOrder: 65, category: 'cadastro', width: 100 },

  // ============================================
  // INFORMAÇÕES ADICIONAIS
  // ============================================
  { id: 'tags', label: 'Tags', defaultVisible: false, defaultOrder: 66, category: 'adicional', width: 150 },
  { id: 'notes', label: 'Notas internas', defaultVisible: false, defaultOrder: 67, category: 'adicional', width: 200 },
  { id: 'additional_data', label: 'Dados adicionais', defaultVisible: false, defaultOrder: 68, category: 'adicional', width: 150 },

  // ============================================
  // TIMESTAMPS
  // ============================================
  { id: 'created_at', label: 'Data de cadastro', defaultVisible: false, defaultOrder: 69, category: 'datas', width: 130, sortable: true },
  { id: 'updated_at', label: 'Última atualização', defaultVisible: false, defaultOrder: 70, category: 'datas', width: 130, sortable: true },
  { id: 'last_contacted_at', label: 'Último contato', defaultVisible: false, defaultOrder: 71, category: 'datas', width: 130, sortable: true },
  { id: 'last_activity_at', label: 'Última atividade', defaultVisible: false, defaultOrder: 72, category: 'datas', width: 130, sortable: true },

  // ============================================
  // BUSCA GLOBAL / PEARCH (campos exclusivos da busca global)
  // ============================================
  { id: 'is_open_to_work', label: 'Open to Work', defaultVisible: false, defaultOrder: 73, category: 'busca_global', width: 100, isGlobalSearch: true },
  { id: 'is_decision_maker', label: 'Decision Maker', defaultVisible: false, defaultOrder: 74, category: 'busca_global', width: 120, isGlobalSearch: true },
  { id: 'is_top_universities', label: 'Top Universities', defaultVisible: false, defaultOrder: 75, category: 'busca_global', width: 130, isGlobalSearch: true },
  { id: 'is_hiring', label: 'Está contratando', defaultVisible: false, defaultOrder: 76, category: 'busca_global', width: 100, isGlobalSearch: true },
  { id: 'headline', label: 'Headline LinkedIn', defaultVisible: false, defaultOrder: 77, category: 'busca_global', width: 250, isGlobalSearch: true },
  { id: 'expertise', label: 'Expertise', defaultVisible: false, defaultOrder: 78, category: 'busca_global', width: 200, isGlobalSearch: true },
  { id: 'linkedin_followers_count', label: 'Seguidores LinkedIn', defaultVisible: false, defaultOrder: 79, category: 'busca_global', width: 120, sortable: true, isGlobalSearch: true },
  { id: 'linkedin_connections_count', label: 'Conexões LinkedIn', defaultVisible: false, defaultOrder: 80, category: 'busca_global', width: 120, sortable: true, isGlobalSearch: true },
  { id: 'outreach_message', label: 'Mensagem de Abordagem', defaultVisible: false, defaultOrder: 81, category: 'busca_global', width: 300, isGlobalSearch: true },
  { id: 'best_personal_email', label: 'Melhor Email Pessoal', defaultVisible: false, defaultOrder: 82, category: 'busca_global', width: 180, isGlobalSearch: true },
  { id: 'phone_types', label: 'Tipos de Telefone', defaultVisible: false, defaultOrder: 83, category: 'busca_global', width: 150, isGlobalSearch: true },
  { id: 'estimated_age', label: 'Idade Estimada', defaultVisible: false, defaultOrder: 84, category: 'busca_global', width: 100, sortable: true, isGlobalSearch: true },
  { id: 'match_reasoning', label: 'Justificativa do Match', defaultVisible: false, defaultOrder: 85, category: 'busca_global', width: 300, isGlobalSearch: true },
  { id: 'overall_summary', label: 'Resumo Geral', defaultVisible: false, defaultOrder: 86, category: 'busca_global', width: 300, isGlobalSearch: true },
  { id: 'query_insights', label: 'Insights por Requisito', defaultVisible: false, defaultOrder: 87, category: 'busca_global', width: 350, isGlobalSearch: true },
  { id: 'pearch_insights', label: 'Insights Pearch', defaultVisible: false, defaultOrder: 88, category: 'busca_global', width: 200, isGlobalSearch: true },
  { id: 'middle_name', label: 'Nome do Meio', defaultVisible: false, defaultOrder: 89, category: 'busca_global', width: 120, isGlobalSearch: true },
  { id: 'best_business_email', label: 'Email Corporativo', defaultVisible: false, defaultOrder: 90, category: 'busca_global', width: 200, isGlobalSearch: true },
  { id: 'personal_emails', label: 'Emails Pessoais', defaultVisible: false, defaultOrder: 91, category: 'busca_global', width: 180, isGlobalSearch: true },
  { id: 'business_emails', label: 'Emails Corporativos', defaultVisible: false, defaultOrder: 92, category: 'busca_global', width: 180, isGlobalSearch: true },
  { id: 'company_followers_count', label: 'Seguidores da Empresa', defaultVisible: false, defaultOrder: 93, category: 'busca_global', width: 130, sortable: true, isGlobalSearch: true },
  { id: 'company_keywords', label: 'Palavras-chave da Empresa', defaultVisible: false, defaultOrder: 94, category: 'busca_global', width: 200, isGlobalSearch: true },
]

export const DEFAULT_COLUMN_WIDTHS: Record<string, number> = {
  checkbox: 50,
  acoes: 120,
  source: 60,
  match_score: 50,
  name: 220,
  id: 100,
  email: 200,
  secondary_email: 200,
  phone: 130,
  mobile_phone: 130,
  secondary_phone: 130,
  linkedin_url: 60,
  github_url: 150,
  portfolio_url: 150,
  date_of_birth: 120,
  gender: 100,
  nationality: 130,
  marital_status: 120,
  cpf: 130,
  current_title: 250,
  current_company: 150,
  seniority_level: 130,
  years_of_experience: 100,
  self_introduction: 200,
  lia_score: 100,
  lia_insights: 200,
  skills_match_percentage: 100,
  technical_skills: 200,
  soft_skills: 180,
  languages: 150,
  certifications: 180,
  interests: 150,
  location_city: 120,
  location_state: 100,
  location_country: 100,
  address_street: 180,
  address_number: 80,
  address_district: 120,
  address_zip: 100,
  address_complement: 150,
  is_remote: 100,
  willing_to_relocate: 100,
  mobility: 100,
  work_model_preference: 130,
  contract_type_preference: 130,
  current_salary: 130,
  salary_currency: 80,
  desired_salary_min: 130,
  desired_salary_max: 130,
  salary_expectation_clt: 130,
  salary_expectation_pj: 130,
  salary_expectation_freelance: 130,
  resume_url: 150,
  resume_text: 200,
  cover_letter: 200,
  ats_source_name: 120,
  ats_candidate_id: 120,
  pearch_profile_id: 120,
  status: 120,
  is_active: 80,
  is_blacklisted: 100,
  blacklist_reason: 150,
  preferred_contact_method: 130,
  best_time_to_contact: 130,
  communication_consent: 100,
  completed_register: 100,
  accept_terms: 100,
  tags: 150,
  notes: 200,
  additional_data: 150,
  created_at: 130,
  updated_at: 130,
  last_contacted_at: 130,
  last_activity_at: 130,
  // Busca Global / Pearch
  is_open_to_work: 100,
  is_decision_maker: 120,
  is_top_universities: 130,
  is_hiring: 100,
  headline: 250,
  expertise: 200,
  linkedin_followers_count: 120,
  linkedin_connections_count: 120,
  outreach_message: 300,
  best_personal_email: 180,
  phone_types: 150,
  estimated_age: 100,
  match_reasoning: 300,
  overall_summary: 300,
  query_insights: 350,
  pearch_insights: 200,
  middle_name: 120,
  best_business_email: 200,
  personal_emails: 180,
  business_emails: 180,
  company_followers_count: 130,
  company_keywords: 200,
  timezone: 140,
  company_hq: 150,
  funding_stage: 140,
  institution_tier: 130,
  company_industries: 180,
  company_size: 140,
}

export function getColumnDefinition(id: string): StandardColumnDefinition | undefined {
  const normalizedId = ID_ALIASES[id] ?? id
  return ALL_COLUMN_DEFINITIONS.find(col => col.id === normalizedId)
}

export function getDefaultTableColumns(): TableColumn[] {
  return ALL_COLUMN_DEFINITIONS.map(col => ({
    id: col.id,
    label: col.label,
    visible: col.defaultVisible,
    order: col.defaultOrder,
    category: col.category,
    sortable: col.sortable,
    width: col.width,
    minWidth: col.minWidth,
    align: col.align,
    isGlobalSearch: col.isGlobalSearch,
  }))
}

export function getVisibleColumns(columns: TableColumn[]): TableColumn[] {
  return columns
    .filter(col => col.visible !== false)
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
}

export function getColumnsByCategory(columns: TableColumn[]): Record<string, TableColumn[]> {
  const byCategory: Record<string, TableColumn[]> = {}
  
  for (const category of COLUMN_CATEGORIES) {
    byCategory[category.id] = columns.filter(col => col.category === category.id)
  }
  
  return byCategory
}

export function toggleColumnVisibility(
  columns: TableColumn[],
  columnId: string
): TableColumn[] {
  return columns.map(col => 
    col.id === columnId 
      ? { ...col, visible: !col.visible }
      : col
  )
}

export function updateColumnOrder(
  columns: TableColumn[],
  columnId: string,
  newOrder: number
): TableColumn[] {
  return columns.map(col =>
    col.id === columnId
      ? { ...col, order: newOrder }
      : col
  )
}

export function reorderColumns(
  columns: TableColumn[],
  draggedId: string,
  targetId: string
): TableColumn[] {
  const draggedIndex = columns.findIndex(c => c.id === draggedId)
  const targetIndex = columns.findIndex(c => c.id === targetId)
  
  if (draggedIndex === -1 || targetIndex === -1) return columns
  
  const newColumns = columns.map(col => ({ ...col }))
  const [draggedColumn] = newColumns.splice(draggedIndex, 1)
  newColumns.splice(targetIndex, 0, draggedColumn)
  
  return newColumns.map((col, index) => ({
    ...col,
    order: index
  }))
}

export function resetColumnsToDefault(): TableColumn[] {
  return getDefaultTableColumns()
}

export interface ColumnPreset {
  id: string
  name: string
  description?: string
  columns: string[]
}

export const COLUMN_PRESETS: ColumnPreset[] = [
  {
    id: 'default',
    name: 'Visualização Padrão',
    description: 'Colunas essenciais para triagem rápida',
    columns: ['source', 'match_score', 'name', 'current_title', 'current_company', 'current_salary', 'desired_salary_max', 'mobile_phone', 'email', 'location_city', 'linkedin_url']
  },
  {
    id: 'contact',
    name: 'Foco em Contato',
    description: 'Todas as informações de contato',
    columns: ['name', 'email', 'secondary_email', 'phone', 'mobile_phone', 'secondary_phone', 'linkedin_url', 'github_url', 'portfolio_url', 'preferred_contact_method', 'best_time_to_contact']
  },
  {
    id: 'professional',
    name: 'Perfil Profissional',
    description: 'Foco em experiência e carreira',
    columns: ['name', 'current_title', 'current_company', 'seniority_level', 'years_of_experience', 'technical_skills', 'certifications', 'languages']
  },
  {
    id: 'salary',
    name: 'Análise Salarial',
    description: 'Todas as informações de remuneração',
    columns: ['name', 'current_title', 'current_company', 'current_salary', 'desired_salary_min', 'desired_salary_max', 'salary_expectation_clt', 'salary_expectation_pj', 'salary_expectation_freelance', 'salary_currency']
  },
  {
    id: 'lia_analysis',
    name: 'Análise LIA',
    description: 'Scores e insights da IA',
    columns: ['name', 'current_title', 'match_score', 'lia_score', 'skills_match_percentage', 'lia_insights', 'technical_skills']
  },
  {
    id: 'compact',
    name: 'Compacto',
    description: 'Apenas nome, cargo e contato principal',
    columns: ['name', 'current_title', 'email', 'mobile_phone', 'location_city']
  },
  {
    id: 'favorites',
    name: 'Favoritos',
    description: 'Visualização otimizada para candidatos favoritos',
    columns: ['name', 'lia_score', 'current_title', 'current_company', 'location_city', 'desired_salary_max', 'linkedin_url']
  },
  {
    id: 'job_kanban',
    name: 'Kanban de Vagas',
    description: 'Visualização otimizada para pipeline de vagas',
    columns: ['name', 'current_title', 'current_company', 'lia_score', 'match_score', 'status']
  },
]

export function applyColumnPreset(
  columns: TableColumn[],
  presetId: string
): TableColumn[] {
  const preset = COLUMN_PRESETS.find(p => p.id === presetId)
  if (!preset) return columns
  
  return columns.map((col, index) => ({
    ...col,
    visible: preset.columns.includes(col.id),
    order: preset.columns.includes(col.id) 
      ? preset.columns.indexOf(col.id)
      : index + 1000
  }))
}
