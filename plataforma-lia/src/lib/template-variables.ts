import { CURRENCY_SYMBOL } from "@/lib/pricing"

export interface TemplateVariable {
  key: string
  label: string
  description: string
  example?: string
}

export interface VariableGroup {
  id: string
  label: string
  icon?: string
  variables: TemplateVariable[]
}

export const VARIABLE_REGISTRY: VariableGroup[] = [
  {
    id: 'candidato',
    label: 'Candidato',
    icon: 'user',
    variables: [
      {
        key: 'candidato_nome',
        label: 'Nome do Candidato',
        description: 'Nome completo do candidato',
        example: 'João Silva'
      },
      {
        key: 'candidate_name',
        label: 'Nome do Candidato (EN)',
        description: 'Nome completo do candidato em inglês',
        example: 'John Smith'
      },
      {
        key: 'user_name',
        label: 'Nome do Usuário',
        description: 'Nome do usuário no sistema',
        example: 'joao.silva'
      },
      {
        key: 'user_email',
        label: 'E-mail do Candidato',
        description: 'Endereço de e-mail do candidato',
        example: 'joao@email.com'
      }
    ]
  },
  {
    id: 'vaga',
    label: 'Vaga',
    icon: 'briefcase',
    variables: [
      {
        key: 'vaga',
        label: 'Título da Vaga',
        description: 'Nome da posição ou cargo',
        example: 'Desenvolvedor Full Stack'
      },
      {
        key: 'job_title',
        label: 'Título da Vaga (EN)',
        description: 'Nome da posição em inglês',
        example: 'Full Stack Developer'
      },
      {
        key: 'department',
        label: 'Departamento',
        description: 'Departamento ou área da vaga',
        example: 'Tecnologia'
      },
      {
        key: 'location',
        label: 'Localização',
        description: 'Local de trabalho da vaga',
        example: 'São Paulo, SP'
      },
      {
        key: 'job_challenge',
        label: 'Desafio da Vaga',
        description: 'Principal desafio ou missão do cargo',
        example: 'Liderar a modernização da plataforma'
      }
    ]
  },
  {
    id: 'empresa',
    label: 'Empresa',
    icon: 'building',
    variables: [
      {
        key: 'empresa_nome',
        label: 'Nome da Empresa',
        description: 'Nome da empresa contratante',
        example: 'Tech Solutions Ltda'
      },
      {
        key: 'company_name',
        label: 'Nome da Empresa (EN)',
        description: 'Nome da empresa em inglês',
        example: 'Tech Solutions Ltd'
      },
      {
        key: 'team_name',
        label: 'Nome do Time',
        description: 'Nome da equipe ou squad',
        example: 'Squad Plataforma'
      }
    ]
  },
  {
    id: 'recrutador',
    label: 'Recrutador',
    icon: 'user-check',
    variables: [
      {
        key: 'recrutador_nome',
        label: 'Nome do Recrutador',
        description: 'Nome do recrutador responsável',
        example: 'Maria Santos'
      },
      {
        key: 'recruiter_name',
        label: 'Nome do Recrutador (EN)',
        description: 'Nome do recrutador em inglês',
        example: 'Mary Santos'
      },
      {
        key: 'interviewer_name',
        label: 'Nome do Entrevistador',
        description: 'Nome de quem vai conduzir a entrevista',
        example: 'Carlos Oliveira'
      },
      {
        key: 'approver_name',
        label: 'Nome do Aprovador',
        description: 'Nome do gestor aprovador',
        example: 'Ana Costa'
      }
    ]
  },
  {
    id: 'entrevista',
    label: 'Entrevista',
    icon: 'calendar',
    variables: [
      {
        key: 'interview_date',
        label: 'Data da Entrevista',
        description: 'Data agendada para a entrevista',
        example: '15/03/2025'
      },
      {
        key: 'interview_time',
        label: 'Horário da Entrevista',
        description: 'Horário agendado para a entrevista',
        example: '14:00'
      },
      {
        key: 'interview_type',
        label: 'Tipo de Entrevista',
        description: 'Formato da entrevista (presencial, remota, etc)',
        example: 'Videochamada'
      },
      {
        key: 'interview_location',
        label: 'Local da Entrevista',
        description: 'Local ou link da entrevista',
        example: 'Google Meet'
      },
      {
        key: 'interview_feedback',
        label: 'Feedback da Entrevista',
        description: 'Retorno sobre a entrevista',
        example: 'Excelente desempenho técnico'
      },
      {
        key: 'calendar_link',
        label: 'Link do Calendário',
        description: 'Link para agendamento no calendário',
        example: 'https://calendar.app.google/...'
      }
    ]
  },
  {
    id: 'metricas',
    label: 'Métricas/Scores',
    icon: 'bar-chart',
    variables: [
      {
        key: 'wsi_score',
        label: 'Score WSI',
        description: 'Pontuação do WorkStyle Index',
        example: '85'
      },
      {
        key: 'match_score',
        label: 'Score de Match',
        description: 'Pontuação de compatibilidade geral',
        example: '92%'
      },
      {
        key: 'skills_score',
        label: 'Score de Habilidades',
        description: 'Pontuação de habilidades técnicas',
        example: '88%'
      },
      {
        key: 'cultural_score',
        label: 'Score Cultural',
        description: 'Pontuação de fit cultural',
        example: '90%'
      },
      {
        key: 'experience_score',
        label: 'Score de Experiência',
        description: 'Pontuação baseada na experiência',
        example: '75%'
      },
      {
        key: 'conversion_rate',
        label: 'Taxa de Conversão',
        description: 'Taxa de conversão do funil',
        example: '45%'
      }
    ]
  },
  {
    id: 'processo',
    label: 'Processo',
    icon: 'git-branch',
    variables: [
      {
        key: 'next_step',
        label: 'Próximo Passo',
        description: 'Próxima etapa do processo seletivo',
        example: 'Entrevista técnica'
      },
      {
        key: 'recommendation',
        label: 'Recomendação',
        description: 'Recomendação sobre o candidato',
        example: 'Recomendado para contratação'
      },
      {
        key: 'feedback',
        label: 'Feedback',
        description: 'Feedback geral do processo',
        example: 'Ótimo desempenho nas etapas'
      },
      {
        key: 'rejection_reason',
        label: 'Motivo da Recusa',
        description: 'Razão para não avançar no processo',
        example: 'Expectativa salarial acima do orçamento'
      },
      {
        key: 'close_reason',
        label: 'Motivo do Fechamento',
        description: 'Razão para fechamento da vaga',
        example: 'Vaga preenchida'
      },
      {
        key: 'start_date',
        label: 'Data de Início',
        description: 'Data prevista para início',
        example: '01/04/2025'
      }
    ]
  },
  {
    id: 'relatorios',
    label: 'Relatórios',
    icon: 'file-text',
    variables: [
      {
        key: 'total_candidates',
        label: 'Total de Candidatos',
        description: 'Número total de candidatos',
        example: '150'
      },
      {
        key: 'hired_count',
        label: 'Contratados',
        description: 'Número de contratações realizadas',
        example: '12'
      },
      {
        key: 'avg_time_to_hire',
        label: 'Tempo Médio de Contratação',
        description: 'Tempo médio do processo seletivo',
        example: '25 dias'
      },
      {
        key: 'cost_per_hire',
        label: 'Custo por Contratação',
        description: 'Custo médio por contratação',
        example: `${CURRENCY_SYMBOL} 2.500`
      },
      {
        key: 'total_hires',
        label: 'Total de Contratações',
        description: 'Total de contratações no período',
        example: '45'
      },
      {
        key: 'interviews_completed',
        label: 'Entrevistas Realizadas',
        description: 'Número de entrevistas concluídas',
        example: '89'
      }
    ]
  },
  {
    id: 'sistema',
    label: 'Sistema',
    icon: 'settings',
    variables: [
      {
        key: 'timestamp',
        label: 'Data/Hora Atual',
        description: 'Data e hora de geração',
        example: '15/03/2025 14:30'
      },
      {
        key: 'date',
        label: 'Data Atual',
        description: 'Data de geração do documento',
        example: '15/03/2025'
      },
      {
        key: 'generated_date',
        label: 'Data de Geração',
        description: 'Data em que foi gerado',
        example: '15/03/2025'
      },
      {
        key: 'generated_time',
        label: 'Hora de Geração',
        description: 'Hora em que foi gerado',
        example: '14:30'
      },
      {
        key: 'action_link',
        label: 'Link de Ação',
        description: 'Link para realizar uma ação',
        example: 'https://app.wedo.ai/action/...'
      },
      {
        key: 'login_link',
        label: 'Link de Login',
        description: 'Link para acessar o sistema',
        example: 'https://app.wedo.ai/login'
      }
    ]
  }
]

export function getAllVariables(): TemplateVariable[] {
  return VARIABLE_REGISTRY.flatMap(group => group.variables)
}

export function getVariableByKey(key: string): TemplateVariable | undefined {
  return getAllVariables().find(v => v.key === key)
}

export function getGroupByVariableKey(key: string): VariableGroup | undefined {
  return VARIABLE_REGISTRY.find(group => 
    group.variables.some(v => v.key === key)
  )
}

export function formatVariable(key: string): string {
  return `{{${key}}}`
}

export function extractVariables(text: string): string[] {
  const regex = /\{\{(\w+)\}\}/g
  const matches: string[] = []
  let match
  while ((match = regex.exec(text)) !== null) {
    matches.push(match[1])
  }
  return [...new Set(matches)]
}

export function validateVariables(text: string): { valid: string[], invalid: string[] } {
  const extracted = extractVariables(text)
  const allVariableKeys = getAllVariables().map(v => v.key)
  
  const valid = extracted.filter(key => allVariableKeys.includes(key))
  const invalid = extracted.filter(key => !allVariableKeys.includes(key))
  
  return { valid, invalid }
}
