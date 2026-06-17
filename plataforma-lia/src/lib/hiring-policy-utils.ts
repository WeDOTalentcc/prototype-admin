export function formatFieldValue(value: unknown): string {
  if (value === null || value === undefined) return "Nao definido"
  if (typeof value === 'boolean') return value ? "Sim" : "Nao"
  if (Array.isArray(value)) {
    if (value.length === 0) return "Nenhum"
    return value.join(', ')
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value)
    if (entries.length === 0) return "Nao definido"
    return entries.map(([k, v]) => `${k}: ${v}`).join(', ')
  }
  return String(value)
}

export type FieldType = 'number' | 'boolean' | 'text' | 'select'

export interface FieldConfig {
  label: string
  type: FieldType
  options?: { value: string; label: string }[]
  placeholder?: string
  min?: number
  max?: number
  suffix?: string
}

export const FIELD_CONFIGS: Record<string, FieldConfig> = {
  min_interviews_before_offer: {
    label: "Min. entrevistas antes da oferta",
    type: 'number',
    min: 0,
    max: 10,
  },
  manager_approval_for_offer: {
    label: "Aprovação Final de Oferta", // distinct from Aprovação de Vaga (job requisition approval in Usuários & Departamentos)
    type: 'boolean',
  },
  max_days_in_stage: {
    label: "Max. dias por etapa",
    type: 'number',
    min: 1,
    max: 90,
    suffix: 'dias',
  },
  allowed_days: {
    label: "Dias permitidos",
    type: 'text',
    placeholder: 'Ex: Seg-Sex',
  },
  allowed_hours: {
    label: "Horario permitido",
    type: 'text',
    placeholder: 'Ex: 09:00-18:00',
  },
  default_duration_minutes: {
    label: "Duracao padrao (min)",
    type: 'number',
    min: 15,
    max: 240,
    suffix: 'min',
  },
  self_scheduling_enabled: {
    label: "Auto-agendamento",
    type: 'boolean',
  },
  auto_rejection_feedback: {
    label: "Feedback automatico de rejeicao",
    type: 'boolean',
  },
  rejection_feedback_deadline_hours: {
    label: "Prazo feedback rejeicao (h)",
    type: 'number',
    min: 1,
    max: 168,
    suffix: 'h',
  },
  preferred_channel: {
    label: "Canal preferido",
    type: 'select',
    options: [
      { value: 'whatsapp', label: 'WhatsApp' },
      { value: 'email', label: 'Email' },
      { value: 'both', label: 'Ambos' },
    ],
  },
  lia_tone: {
    label: "Tom da IA",
    type: 'select',
    options: [
      { value: 'professional', label: 'Profissional' },
      { value: 'friendly', label: 'Amigavel' },
      { value: 'formal', label: 'Formal' },
    ],
  },
  salary_expectation_filter: {
    label: "Filtro de pretensao salarial",
    type: 'boolean',
  },
  salary_tolerance_percent: {
    label: "Tolerancia salarial (%)",
    type: 'number',
    min: 0,
    max: 100,
    suffix: '%',
  },
  experience_policy: {
    label: "Politica de experiencia",
    type: 'select',
    options: [
      { value: 'per_job', label: 'Por vaga' },
      { value: 'global', label: 'Global' },
    ],
  },
  default_screening_questions: {
    label: "Perguntas padrao de triagem",
    type: 'text',
    placeholder: 'Separadas por virgula',
  },
  auto_screening: {
    label: "Triagem automatica",
    type: 'boolean',
  },
  auto_scheduling: {
    label: "Agendamento automatico",
    type: 'boolean',
  },
  auto_stage_advance: {
    label: "Avanco automatico de etapa",
    type: 'boolean',
  },
  autonomy_level: {
    label: "Nivel de autonomia",
    type: 'select',
    options: [
      { value: 'low', label: 'Baixo' },
      { value: 'medium', label: 'Medio' },
      { value: 'high', label: 'Alto' },
    ],
  },
  requires_validation_before_shortlist: {
    label: "Validacao humana antes do shortlist",
    type: 'boolean',
  },
  auto_send_negative_feedback: {
    label: "Envio automatico de feedback negativo",
    type: 'boolean',
  },
  auto_schedule_interviews: {
    label: "Agendamento automatico de entrevistas",
    type: 'boolean',
  },
}

export const FIELD_LABELS: Record<string, string> = Object.fromEntries(
  Object.entries(FIELD_CONFIGS).map(([key, config]) => [key, config.label])
)

export const POLICY_BLOCKS = [
  {
    key: 'pipeline_rules',
    title: 'Pipeline e Processo',
    iconName: 'GitBranch' as const,
    fields: ['min_interviews_before_offer', 'manager_approval_for_offer', 'max_days_in_stage']
  },
  {
    key: 'scheduling_rules',
    title: 'Agendamento',
    iconName: 'Calendar' as const,
    fields: ['allowed_days', 'allowed_hours', 'default_duration_minutes', 'self_scheduling_enabled']
  },
  {
    key: 'communication_rules',
    title: 'Comunicacao',
    iconName: 'MessageSquare' as const,
    fields: ['auto_rejection_feedback', 'rejection_feedback_deadline_hours', 'preferred_channel', 'lia_tone']
  },
  {
    key: 'screening_rules',
    title: 'Triagem',
    iconName: 'Filter' as const,
    fields: ['salary_expectation_filter', 'salary_tolerance_percent', 'experience_policy', 'default_screening_questions']
  },
  {
    key: 'automation_rules',
    title: 'Autonomia da IA',
    iconName: 'Zap' as const,
    fields: [
      'auto_screening', 'auto_scheduling', 'auto_stage_advance', 'autonomy_level',
      'auto_schedule_interviews', 'auto_send_negative_feedback', 'requires_validation_before_shortlist',
    ]
  },
]
