import { CURRENCY_SYMBOL } from "@/lib/pricing"
import type { ATSSystem, Integration, SyncLog, SystemField, MappingTemplate } from './ats-integrations.types'

export const ATS_SYSTEMS: ATSSystem[] = [
  {
    id: 'sap_sf',
    name: 'SAP SuccessFactors',
    type: 'sap',
    status: 'connected',
    description: 'Sistema completo de gestão de recursos humanos',
    logo: 'https://logos-world.net/wp-content/uploads/2020/04/SAP-Logo.png',
    lastSync: '2024-01-20T14:30:00Z',
    totalRecords: 2847,
    syncedRecords: 2847,
    errorCount: 0,
    features: ['Candidatos', 'Vagas', 'Entrevistas', 'Ofertas', 'Onboarding'],
    webhookUrl: 'https://api.plataforma-lia.com/webhooks/sap',
    apiEndpoint: 'https://api.successfactors.com/v2',
    version: '2.0'
  },
  {
    id: 'workday',
    name: 'Workday HCM',
    type: 'workday',
    status: 'connecting',
    description: 'Plataforma de capital humano empresarial',
    logo: 'https://logos-world.net/wp-content/uploads/2021/08/Workday-Logo.png',
    totalRecords: 0,
    syncedRecords: 0,
    errorCount: 0,
    features: ['Funcionários', 'Requisições', 'Performance', 'Benefícios'],
    apiEndpoint: 'https://wd2-impl-services1.workday.com',
    version: '39.0'
  },
  {
    id: 'bamboohr',
    name: 'BambooHR',
    type: 'bamboohr',
    status: 'error',
    description: 'Sistema de RH para pequenas e médias empresas',
    logo: 'https://www.bamboohr.com/images/bamboo-logo.svg',
    lastSync: '2024-01-19T16:20:00Z',
    totalRecords: 156,
    syncedRecords: 134,
    errorCount: 22,
    features: ['Colaboradores', 'Relatórios', 'Time Off', 'Performance'],
    webhookUrl: 'https://api.plataforma-lia.com/webhooks/bamboo',
    apiEndpoint: 'https://api.bamboohr.com/api/gateway.php',
    version: '1.0'
  },
  {
    id: 'greenhouse',
    name: 'Greenhouse',
    type: 'greenhouse',
    status: 'disabled',
    description: 'ATS focado em recrutamento e seleção',
    logo: 'https://greenhouse-production.s3.amazonaws.com/assets/logos/greenhouse_logo_full_color-7b8b4bad0fe1e2b667ad1ff3d5b41a84.svg',
    totalRecords: 0,
    syncedRecords: 0,
    errorCount: 0,
    features: ['Candidatos', 'Vagas', 'Entrevistas', 'Scorecards'],
    apiEndpoint: 'https://harvest.greenhouse.io/v1',
    version: '1.0'
  }
]

export const INTEGRATIONS: Integration[] = [
  {
    id: 'sap_candidates',
    name: 'Sincronização de Candidatos',
    system: ATS_SYSTEMS[0],
    isActive: true,
    lastRun: '2024-01-20T14:30:00Z',
    nextRun: '2024-01-20T15:30:00Z',
    frequency: 'hourly',
    direction: 'bidirectional',
    mappedFields: 24,
    totalFields: 32
  },
  {
    id: 'sap_jobs',
    name: 'Importação de Vagas',
    system: ATS_SYSTEMS[0],
    isActive: true,
    lastRun: '2024-01-20T14:15:00Z',
    nextRun: '2024-01-21T14:15:00Z',
    frequency: 'daily',
    direction: 'import',
    mappedFields: 18,
    totalFields: 25
  },
  {
    id: 'bamboo_employees',
    name: 'Dados de Funcionários',
    system: ATS_SYSTEMS[2],
    isActive: false,
    lastRun: '2024-01-19T16:20:00Z',
    nextRun: '2024-01-20T16:20:00Z',
    frequency: 'daily',
    direction: 'import',
    mappedFields: 12,
    totalFields: 20
  }
]

export const SYNC_LOGS: SyncLog[] = [
  {
    id: '1',
    timestamp: '2024-01-20T14:30:00Z',
    system: 'SAP SuccessFactors',
    type: 'sync',
    status: 'success',
    records: 15,
    duration: 2340,
    message: 'Sincronização de candidatos concluída com sucesso',
    details: '15 novos candidatos importados, 3 atualizados'
  },
  {
    id: '2',
    timestamp: '2024-01-20T14:15:00Z',
    system: 'SAP SuccessFactors',
    type: 'webhook',
    status: 'success',
    records: 1,
    duration: 156,
    message: 'Nova vaga recebida via webhook',
    details: 'Vaga "Senior Developer" criada automaticamente'
  },
  {
    id: '3',
    timestamp: '2024-01-19T16:20:00Z',
    system: 'BambooHR',
    type: 'sync',
    status: 'error',
    records: 0,
    duration: 5000,
    message: 'Erro de autenticação na API',
    details: 'Token de acesso expirado - necessária renovação manual'
  },
  {
    id: '4',
    timestamp: '2024-01-19T12:00:00Z',
    system: 'SAP SuccessFactors',
    type: 'manual',
    status: 'warning',
    records: 234,
    duration: 12450,
    message: 'Sincronização manual com avisos',
    details: '234 registros processados, 12 campos não mapeados encontrados'
  }
]

export const LIA_FIELDS: SystemField[] = [
  { id: 'candidate_id', name: 'ID do Candidato', type: 'string', required: true, description: 'Identificador único na LIA' },
  { id: 'nome_completo', name: 'Nome Completo', type: 'string', required: true, description: 'Nome completo do candidato' },
  { id: 'email_principal', name: 'Email Principal', type: 'email', required: true, description: 'Email principal de contato' },
  { id: 'telefone_contato', name: 'Telefone', type: 'phone', required: false, description: 'Telefone principal' },
  { id: 'cargo_pretendido', name: 'Cargo Pretendido', type: 'string', required: true, description: 'Posição desejada' },
  { id: 'departamento_alvo', name: 'Departamento', type: 'string', required: false, description: 'Departamento de interesse' },
  { id: 'anos_experiencia', name: 'Anos de Experiência', type: 'number', required: false, description: 'Total de anos de experiência' },
  { id: 'url_curriculo', name: 'URL do Currículo', type: 'url', required: false, description: 'Link para o currículo' },
  { id: 'data_candidatura', name: 'Data da Candidatura', type: 'date', required: true, description: 'Data de aplicação' },
  { id: 'status_processo', name: 'Status do Processo', type: 'select', required: true, description: 'Situação atual no processo seletivo' },
  { id: 'pretensao_salarial', name: 'Pretensão Salarial', type: 'number', required: false, description: `Expectativa salarial em ${CURRENCY_SYMBOL}` },
  { id: 'score_lia', name: 'Score', type: 'number', required: false, description: 'Score de compatibilidade calculado por IA' }
]

export const MAPPING_TEMPLATES: MappingTemplate[] = [
  {
    id: 'standard',
    name: 'Mapeamento Padrão',
    description: 'Mapeamento básico para campos comuns',
    mappings: [
      { sourceField: 'candidate_id', targetField: 'candidate_id', confidence: 100 },
      { sourceField: 'first_name', targetField: 'nome_completo', confidence: 90 },
      { sourceField: 'email', targetField: 'email_principal', confidence: 100 },
      { sourceField: 'phone', targetField: 'telefone_contato', confidence: 100 },
      { sourceField: 'position_applied', targetField: 'cargo_pretendido', confidence: 95 }
    ]
  },
  {
    id: 'complete',
    name: 'Mapeamento Completo',
    description: 'Mapeamento abrangente incluindo campos opcionais',
    mappings: [
      { sourceField: 'candidate_id', targetField: 'candidate_id', confidence: 100 },
      { sourceField: 'first_name', targetField: 'nome_completo', confidence: 90 },
      { sourceField: 'email', targetField: 'email_principal', confidence: 100 },
      { sourceField: 'phone', targetField: 'telefone_contato', confidence: 100 },
      { sourceField: 'position_applied', targetField: 'cargo_pretendido', confidence: 95 },
      { sourceField: 'department', targetField: 'departamento_alvo', confidence: 85 },
      { sourceField: 'experience_years', targetField: 'anos_experiencia', confidence: 100 },
      { sourceField: 'resume_url', targetField: 'url_curriculo', confidence: 100 },
      { sourceField: 'application_date', targetField: 'data_candidatura', confidence: 100 },
      { sourceField: 'current_status', targetField: 'status_processo', confidence: 90 },
      { sourceField: 'salary_expectation', targetField: 'pretensao_salarial', confidence: 95 }
    ]
  }
]

export const SAP_FIELDS: SystemField[] = [
  { id: 'candidate_id', name: 'Candidate ID', type: 'string', required: true, description: 'Identificador único do candidato' },
  { id: 'first_name', name: 'First Name', type: 'string', required: true, description: 'Primeiro nome' },
  { id: 'last_name', name: 'Last Name', type: 'string', required: true, description: 'Sobrenome' },
  { id: 'email', name: 'Email Address', type: 'email', required: true, description: 'Email principal' },
  { id: 'phone', name: 'Phone Number', type: 'phone', required: false, description: 'Telefone de contato' },
  { id: 'position_applied', name: 'Position Applied', type: 'string', required: true, description: 'Cargo aplicado' },
  { id: 'department', name: 'Department', type: 'string', required: false, description: 'Departamento' },
  { id: 'experience_years', name: 'Years of Experience', type: 'number', required: false, description: 'Anos de experiência' },
  { id: 'resume_url', name: 'Resume URL', type: 'url', required: false, description: 'Link do currículo' },
  { id: 'application_date', name: 'Application Date', type: 'date', required: true, description: 'Data da candidatura' },
  { id: 'current_status', name: 'Current Status', type: 'select', required: true, description: 'Status atual no processo' },
  { id: 'salary_expectation', name: 'Salary Expectation', type: 'number', required: false, description: 'Expectativa salarial' }
]

export const DEFAULT_FIELDS: SystemField[] = [
  { id: 'id', name: 'ID', type: 'string', required: true, description: 'Identificador único' },
  { id: 'name', name: 'Full Name', type: 'string', required: true, description: 'Nome completo' },
  { id: 'email', name: 'Email', type: 'email', required: true, description: 'Email' },
  { id: 'phone', name: 'Phone', type: 'phone', required: false, description: 'Telefone' },
  { id: 'position', name: 'Position', type: 'string', required: true, description: 'Cargo' },
  { id: 'status', name: 'Status', type: 'select', required: true, description: 'Status' }
]

export const FIELD_TYPE_ICONS: Record<string, string> = {
  string: '📝',
  email: '📧',
  phone: '📞',
  number: '🔢',
  date: '📅',
  url: '🔗',
  select: '📋'
}

export const VIEW_TABS = [
  { id: 'overview' as const, label: 'Visão Geral', iconName: 'BarChart3' },
  { id: 'systems' as const, label: 'Sistemas', iconName: 'Server' },
  { id: 'integrations' as const, label: 'Integrações', iconName: 'Settings' },
  { id: 'logs' as const, label: 'Logs', iconName: 'FileText' }
]

export const MODAL_TABS = [
  { id: 'connection' as const, label: 'Conexão', iconName: 'Link2' },
  { id: 'mapping' as const, label: 'Mapeamento', iconName: 'GitBranch' },
  { id: 'sync' as const, label: 'Sincronização', iconName: 'RefreshCw' },
  { id: 'webhooks' as const, label: 'Webhooks', iconName: 'Zap' }
]
