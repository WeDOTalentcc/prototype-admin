"use client"

import { CURRENCY_SYMBOL } from "@/lib/pricing"
import type { PendingTask, ActiveAlert, Task, JobWithAlert, JobRequest } from "./use-tasks-core"

export const MOCK_PENDING_TASKS: PendingTask[] = [
  {
    id: 'pt-1',
    title: 'Feedback de Entrevista Técnica',
    description: 'Avaliar candidato João Silva após entrevista de React',
    type: 'feedback',
    priority: 'high',
    dueDate: new Date(2025, 10, 29, 14, 0),
    relatedJob: 'UX Designer Sênior',
    candidateName: 'João Silva',
    createdAt: new Date(2025, 10, 28, 10, 0)
  },
  {
    id: 'pt-2',
    title: 'Agendar Entrevista Final',
    description: 'Coordenar horário com gestor para candidato aprovado',
    type: 'entrevista',
    priority: 'medium',
    dueDate: new Date(2025, 10, 30, 11, 0),
    relatedJob: 'Desenvolvedor React Sênior',
    candidateName: 'Maria Santos',
    createdAt: new Date(2025, 10, 27, 16, 0)
  },
  {
    id: 'pt-3',
    title: 'Sourcing de Candidatos',
    description: 'Buscar 10 perfis de Data Scientists no LinkedIn',
    type: 'sourcing',
    priority: 'medium',
    dueDate: new Date(2025, 11, 1, 18, 0),
    relatedJob: 'Data Scientist',
    createdAt: new Date(2025, 10, 26, 9, 0)
  },
  {
    id: 'pt-4',
    title: 'Feedback de Fit Cultural',
    description: 'Validar alinhamento de valores do candidato',
    type: 'feedback',
    priority: 'low',
    dueDate: new Date(2025, 11, 2, 10, 0),
    relatedJob: 'Gerente de Vendas',
    candidateName: 'Carlos Oliveira',
    createdAt: new Date(2025, 10, 25, 14, 0)
  },
  {
    id: 'pt-5',
    title: 'Confirmar Entrevista',
    description: 'Reconfirmar disponibilidade do candidato',
    type: 'entrevista',
    priority: 'high',
    dueDate: new Date(2025, 10, 29, 9, 0),
    relatedJob: 'UX Designer Pleno',
    candidateName: 'Ana Costa',
    createdAt: new Date(2025, 10, 28, 8, 0)
  }
]

export const MOCK_ACTIVE_ALERTS: ActiveAlert[] = [
  {
    id: 'alert-1',
    title: 'Candidatos sem contato há 5+ dias',
    description: '3 candidatos aguardando retorno na vaga de UX Designer',
    severity: 'high',
    jobId: 'WDT-2025-001',
    jobTitle: 'UX Designer Sênior',
    createdAt: new Date(2025, 10, 28, 8, 0),
    action: 'Enviar follow-up automático'
  },
  {
    id: 'alert-2',
    title: 'Prazo de preenchimento próximo',
    description: 'Vaga de React Sênior deve ser preenchida em 7 dias',
    severity: 'medium',
    jobId: 'WDT-2025-002',
    jobTitle: 'Desenvolvedor React Sênior',
    createdAt: new Date(2025, 10, 27, 14, 0),
    action: 'Acelerar processo'
  },
  {
    id: 'alert-3',
    title: 'Taxa de conversão baixa',
    description: 'Apenas 15% dos candidatos passam da triagem',
    severity: 'medium',
    jobId: 'WDT-2025-004',
    jobTitle: 'Data Scientist',
    createdAt: new Date(2025, 10, 26, 10, 0),
    action: 'Revisar requisitos'
  },
  {
    id: 'alert-4',
    title: 'Feedback pendente do gestor',
    description: 'Roberto Silva não respondeu avaliação há 3 dias',
    severity: 'low',
    jobId: 'WDT-2025-001',
    jobTitle: 'UX Designer Sênior',
    createdAt: new Date(2025, 10, 25, 16, 0),
    action: 'Cobrar gestor'
  }
]

export const MOCK_TASKS: Task[] = [
  { id: '1', title: 'Entrevista Técnica - João Silva', description: 'Frontend Developer • React + TypeScript', type: 'entrevista', status: 'pending', dueDate: new Date(2025, 9, 11, 9, 0), priority: 'high', relatedTo: 'UX Designer Sênior', color: 'border-l-lia-border-strong dark:border-l-lia-border-default' },
  { id: '2', title: 'Enviar Lembrete', description: 'Entrevista João Silva - 09:00', type: 'ia', status: 'pending', dueDate: new Date(2025, 9, 11, 8, 45), priority: 'medium', relatedTo: 'Lembrete automático', color: 'border-l-lia-border-strong dark:border-l-lia-border-default' },
  { id: '3', title: 'Revisar CVs - Backend Dev', description: '15 candidatos pendentes', type: 'minha', status: 'pending', dueDate: new Date(2025, 9, 11, 10, 30), priority: 'medium', relatedTo: 'Triagem inicial', color: 'border-l-lia-border-medium' },
  { id: '4', title: 'Revisar Perfis', description: '15 candidatos pendentes • Sugestão LIA', type: 'ia', status: 'pending', dueDate: new Date(2025, 9, 11, 11, 0), priority: 'medium', relatedTo: 'Triagem rápida', color: 'border-l-lia-border-strong dark:border-l-lia-border-default' },
  { id: '5', title: 'Autorizar Feedback - Ana Costa', description: 'UX Designer • Processo finalizado', type: 'minha', status: 'pending', dueDate: new Date(2025, 9, 11, 14, 0), priority: 'high', relatedTo: 'Aprovação necessária', color: 'border-l-lia-border-strong dark:border-l-lia-border-default' },
  { id: '6', title: 'Publicar Vaga - UX Designer', description: 'Área de Produto • Revisão final', type: 'minha', status: 'pending', dueDate: new Date(2025, 9, 11, 15, 30), priority: 'medium', relatedTo: 'Publicação em 3 canais', color: 'border-l-lia-border-strong dark:border-l-lia-border-default' },
  { id: '7', title: 'Aprovar Oferta', description: 'Lucas Mendes - Backend • Sugestão LIA', type: 'ia', status: 'pending', dueDate: new Date(2025, 9, 11, 16, 0), priority: 'high', relatedTo: `Oferta ${CURRENCY_SYMBOL} 12.000`, color: 'border-l-lia-border-strong dark:border-l-lia-border-default' },
  { id: '8', title: 'Enviar Oferta - Lucas Mendes', description: 'Backend Developer • Aprovado', type: 'oferta', status: 'pending', dueDate: new Date(2025, 9, 11, 16, 30), priority: 'high', relatedTo: `${CURRENCY_SYMBOL} 12.000`, color: 'border-l-lia-border-strong dark:border-l-lia-border-default' }
]

export const MOCK_JOBS_WITH_ALERTS: JobWithAlert[] = [
  {
    id: '1', jobId: 'WDT-2025-001', title: 'UX Designer Sênior', department: 'Design', stage: 'Entrevistas',
    totalCandidates: 45, manager: 'Roberto Silva', managerEmail: 'roberto.silva@sodexo.com',
    openDate: '2025-03-01', daysOpen: 28, urgencyLevel: 'urgent', budget: 25000, budgetUsed: 18500,
    publishedLinkedIn: true, publishedWebsite: true, publishedIndeed: true,
    stages: { new: 12, uncontacted: 8, contacted: 15, replied: 10, phoneScreen: 7, onsite: 4, makeOffer: 2, hired: 0 },
    alert: { type: 'urgent', message: '3 candidatos aguardando feedback há 5+ dias', action: 'Enviar feedbacks' },
    liaPendencies: ['Aprovar feedback de Ana Costa', 'Agendar entrevista com João Silva', 'Responder candidato Pedro Alves']
  },
  {
    id: '2', jobId: 'WDT-2025-002', title: 'Desenvolvedor React Sênior', department: 'Tecnologia', stage: 'Finalização',
    totalCandidates: 68, manager: 'Carlos Santos', managerEmail: 'carlos.santos@sodexo.com',
    openDate: '2025-02-15', daysOpen: 42, urgencyLevel: 'critical', budget: 35000, budgetUsed: 32000,
    publishedLinkedIn: true, publishedWebsite: false, publishedIndeed: true,
    stages: { new: 5, uncontacted: 2, contacted: 8, replied: 12, phoneScreen: 10, onsite: 6, makeOffer: 3, hired: 2 },
    alert: { type: 'success', message: '2 ofertas aceitas - preparar onboarding', action: 'Iniciar onboarding' },
    liaPendencies: ['Preparar onboarding de Carlos M.', 'Negociar data de início']
  },
  {
    id: '3', jobId: 'WDT-2025-004', title: 'Data Scientist', department: 'Tecnologia', stage: 'Triagem',
    totalCandidates: 52, manager: 'Roberto Silva', managerEmail: 'roberto.silva@sodexo.com',
    openDate: '2025-02-20', daysOpen: 15, urgencyLevel: 'normal', budget: 60000, budgetUsed: 45000,
    publishedLinkedIn: true, publishedWebsite: true, publishedIndeed: false,
    stages: { new: 23, uncontacted: 15, contacted: 8, replied: 4, phoneScreen: 2, onsite: 0, makeOffer: 0, hired: 0 },
    alert: { type: 'warning', message: 'Taxa de resposta baixa (26%) - revisar abordagem', action: 'Otimizar outreach' },
    liaPendencies: ['Finalizar triagem automática', 'Preparar teste prático']
  }
]

export const MOCK_JOB_REQUESTS: JobRequest[] = [
  {
    id: '1', requestId: 'REQ-2025-045', title: 'Desenvolvedor Full Stack Sênior', department: 'Tecnologia',
    requester: 'Carlos Mendes', requesterEmail: 'carlos.mendes@sodexo.com', requestDate: '2025-10-05',
    status: 'pending_approval', priority: 'critical', headcount: 2, estimatedSalary: `${CURRENCY_SYMBOL} 12.000 - ${CURRENCY_SYMBOL} 15.000`,
    workModel: 'hybrid', justification: 'Expansão do time de produto para atender demanda de novos projetos estratégicos.',
    approvers: [
      { name: 'Roberto Silva', role: 'Diretor de Tecnologia', status: 'approved', date: '2025-10-06', comments: 'Aprovado. Projeto crítico.' },
      { name: 'Ana Costa', role: 'VP de Operações', status: 'pending' },
      { name: 'Pedro Souza', role: 'CFO', status: 'pending' }
    ], daysWaiting: 6
  },
  {
    id: '2', requestId: 'REQ-2025-046', title: 'UX Designer Pleno', department: 'Design',
    requester: 'Juliana Oliveira', requesterEmail: 'juliana.oliveira@sodexo.com', requestDate: '2025-10-08',
    status: 'in_review', priority: 'high', headcount: 1, estimatedSalary: `${CURRENCY_SYMBOL} 8.000 - ${CURRENCY_SYMBOL} 10.000`,
    workModel: 'remote', justification: 'Necessidade de reforço no time para redesign da plataforma mobile.',
    approvers: [
      { name: 'Roberto Silva', role: 'Head de Design', status: 'approved', date: '2025-10-09', comments: 'Aprovado com ressalvas sobre budget' },
      { name: 'Ana Costa', role: 'VP de Operações', status: 'pending' }
    ], daysWaiting: 3
  },
  {
    id: '3', requestId: 'REQ-2025-047', title: 'Analista de Marketing Digital', department: 'Marketing',
    requester: 'Marina Santos', requesterEmail: 'marina.santos@sodexo.com', requestDate: '2025-10-09',
    status: 'requires_changes', priority: 'medium', headcount: 1, estimatedSalary: `${CURRENCY_SYMBOL} 6.000 - ${CURRENCY_SYMBOL} 8.000`,
    workModel: 'hybrid', justification: 'Reforço para campanhas de lançamento de novos produtos.',
    approvers: [
      { name: 'Paula Lima', role: 'Diretora de Marketing', status: 'rejected', date: '2025-10-10', comments: 'Solicito revisão do budget e escopo' }
    ], daysWaiting: 2
  },
  {
    id: '4', requestId: 'REQ-2025-048', title: 'Gerente de Vendas - Região Sul', department: 'Vendas',
    requester: 'Fernando Costa', requesterEmail: 'fernando.costa@sodexo.com', requestDate: '2025-10-01',
    status: 'approved', priority: 'high', headcount: 1, estimatedSalary: `${CURRENCY_SYMBOL} 15.000 - ${CURRENCY_SYMBOL} 18.000`,
    workModel: 'hybrid', justification: 'Expansão da operação comercial na região Sul.',
    approvers: [
      { name: 'Ricardo Alves', role: 'VP de Vendas', status: 'approved', date: '2025-10-02', comments: 'Aprovado. Iniciar processo imediatamente.' },
      { name: 'Pedro Souza', role: 'CFO', status: 'approved', date: '2025-10-03', comments: 'Budget aprovado' }
    ], daysWaiting: 10
  },
  {
    id: '5', requestId: 'REQ-2025-049', title: 'Assistente Administrativo', department: 'Operações',
    requester: 'Carla Mendes', requesterEmail: 'carla.mendes@sodexo.com', requestDate: '2025-10-10',
    status: 'draft', priority: 'low', headcount: 1, estimatedSalary: `${CURRENCY_SYMBOL} 3.500 - ${CURRENCY_SYMBOL} 4.500`,
    workModel: 'onsite', justification: 'Reposição de colaborador que será promovido internamente.',
    approvers: [{ name: 'Ana Costa', role: 'VP de Operações', status: 'pending' }],
    daysWaiting: 1
  }
]
