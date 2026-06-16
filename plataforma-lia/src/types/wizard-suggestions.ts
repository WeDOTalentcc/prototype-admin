export type DataSource = 
  | 'company_settings' 
  | 'lia_history' 
  | 'imported_ats' 
  | 'workforce_planning' 
  | 'curated_templates';

export interface Suggestion {
  value: unknown;
  source: DataSource;
  confidence: number;
  explanation: string;
  metadata?: Record<string, unknown>;
}

export interface FieldSuggestionResponse {
  field: string;
  best_suggestion: Suggestion | null;
  all_suggestions: Suggestion[];
}

export interface AllSuggestionsRequest {
  job_title?: string;
  department?: string;
  seniority?: string;
  location?: string;
  work_model?: string;
  employment_type?: string;
  fields?: string[];
}

export interface AllSuggestionsResponse {
  suggestions: Record<string, FieldSuggestionResponse>;
  context: {
    job_title?: string;
    department?: string;
    seniority?: string;
  };
}

export interface SimilarJob {
  id: string;
  source: DataSource;
  title: string;
  department?: string;
  seniority?: string;
  was_successful?: boolean;
  time_to_fill?: number;
  created_at: string;
  can_use_as_template: boolean;
}

export interface DataCoverageSource {
  name: string;
  precision: string;
  description: string;
}

export interface DataCoverage {
  imported_jds: number;
  skills_catalog: number;
  job_patterns: number;
  coverage_score: number;
  recommendations: string[];
  sources: Record<string, DataCoverageSource>;
}

export interface SourcePriority {
  source: DataSource;
  priority: number;
  confidence: number;
  description: string;
}

export interface WizardSuggestionContext {
  job_title?: string;
  department?: string;
  seniority?: string;
  location?: string;
  work_model?: string;
  employment_type?: string;
}

export const WIZARD_FIELDS = [
  'job_title',
  'department', 
  'seniority',
  'salary_range',
  'technical_skills',
  'behavioral_competencies',
  'responsibilities',
  'benefits',
  'work_model',
  'location'
] as const;

export type WizardField = typeof WIZARD_FIELDS[number];

export const SOURCE_LABELS: Record<DataSource, string> = {
  'company_settings': 'Configurações',
  'lia_history': 'Histórico',
  'imported_ats': 'ATS Importado',
  'workforce_planning': 'Planejamento',
  'curated_templates': 'Template'
};

export const SOURCE_COLORS: Record<DataSource, string> = {
  'company_settings': 'bg-wedo-cyan/15 text-wedo-cyan-text',
  'lia_history': 'bg-status-success/15 text-status-success',
  'imported_ats': 'bg-wedo-purple/15 text-wedo-purple-text',
  'workforce_planning': 'bg-wedo-orange/15 text-wedo-orange-text',
  'curated_templates': 'bg-lia-bg-tertiary text-lia-text-primary'
};
