/**
 * Tipos para Job Description
 * 
 * Correspondem aos schemas Pydantic do backend:
 * - JD Preview (v1): Para validação com indicadores de sugestão
 * - JD Final (v2): Para publicação
 */

export type SuggestionSource = 
  | 'detected'
  | 'lia_catalog'
  | 'lia_market'
  | 'company_default'
  | 'recruiter';

export type RequirementLevel = 'required' | 'nice_to_have';

export type WorkModel = 'remoto' | 'hibrido' | 'presencial';

export type ContractType = 'CLT' | 'PJ' | 'Estágio' | 'Temporário' | 'Freelancer';

export type Priority = 'baixa' | 'media' | 'alta' | 'urgente';

export interface Responsibility {
  description: string;
  source: SuggestionSource;
  is_new: boolean;
}

export interface Competency {
  name: string;
  level: RequirementLevel;
  source: SuggestionSource;
  years_experience?: number;
  proficiency?: string;
  is_new: boolean;
}

export interface Benefit {
  name: string;
  description?: string;
  value?: string;
}

export interface CompensationData {
  salary_min?: number;
  salary_max?: number;
  salary_currency: string;
  show_salary: boolean;
  bonus_percentage?: number;
  bonus_description?: string;
  plr?: string;
  equity?: string;
  benefits: Benefit[];
  market_comparison?: string;
  market_percentile?: number;
  has_alert: boolean;
  alert_message?: string;
}

export interface InterviewStage {
  order: number;
  name: string;
  format?: string;
  duration?: string;
  description?: string;
  responsible?: string;
  responsible_email?: string;
}

export interface CompanyValue {
  name: string;
  description: string;
}

export interface CompanyEVP {
  impact?: string;
  growth?: string;
  team?: string;
  flexibility?: string;
  benefits?: string;
}

export interface CompanyInfo {
  name: string;
  about?: string;
  mission?: string;
  size?: string;
  industry?: string;
  values: CompanyValue[];
  evp?: CompanyEVP;
  diversity_statement?: string;
  careers_url?: string;
  contact_email?: string;
}

export interface HiringManager {
  name: string;
  email: string;
  department?: string;
}

export interface JobMetadata {
  hiring_manager?: HiringManager;
  is_confidential: boolean;
  priority: Priority;
  open_date?: string;
  target_date?: string;
  sla_days?: number;
}

export interface JobDescriptionPreviewData {
  title: string;
  department?: string;
  seniority?: string;
  num_positions: number;
  work_model: WorkModel;
  office_days_per_week?: number;
  contract_type: ContractType;
  location?: string;
  is_affirmative: boolean;
  affirmative_type?: string;
  description?: string;
  responsibilities: Responsibility[];
  technical_competencies: Competency[];
  behavioral_competencies: Competency[];
  compensation?: CompensationData;
  company?: CompanyInfo;
  suggestions_count: number;
  alerts_count: number;
  completeness_score: number;
}

export interface JobDescriptionFinalData {
  title: string;
  department?: string;
  seniority?: string;
  num_positions: number;
  work_model: WorkModel;
  office_days_per_week?: number;
  contract_type: ContractType;
  location?: string;
  is_affirmative: boolean;
  affirmative_type?: string;
  description?: string;
  responsibilities: string[];
  required_technical: string[];
  required_behavioral: string[];
  nice_to_have: string[];
  compensation?: CompensationData;
  company?: CompanyInfo;
  interview_process: InterviewStage[];
  total_timeline?: string;
  apply_url?: string;
  contact_email?: string;
  metadata?: JobMetadata;
  generated_at: string;
}

export const SECTION_TITLES = {
  about: "Sobre a Empresa",
  the_role: "A Vaga",
  what_you_will_do: "O Que Você Vai Fazer",
  what_we_are_looking_for: "O Que Buscamos",
  required: "Requisitos Obrigatórios",
  nice_to_have: "Diferenciais",
  technical: "Competências Técnicas",
  behavioral: "Competências Comportamentais",
  why_join_us: "Por Que Trabalhar Conosco?",
  compensation: "Remuneração",
  benefits: "Benefícios",
  our_values: "Nossos Valores",
  interview_process: "Processo Seletivo",
  diversity: "Diversidade e Inclusão",
  apply: "Como se Candidatar",
  questions: "Dúvidas?",
} as const;

export const WORK_MODEL_LABELS: Record<WorkModel, string> = {
  remoto: "100% Remoto",
  hibrido: "Híbrido",
  presencial: "Presencial",
};

export const CONTRACT_TYPE_LABELS: Record<ContractType, string> = {
  CLT: "CLT",
  PJ: "PJ",
  Estágio: "Estágio",
  Temporário: "Temporário",
  Freelancer: "Freelancer",
};

export const SUGGESTION_INDICATOR = "💡";
export const ALERT_INDICATOR = "⚠️";
export const NEW_INDICATOR = "✨";
