export interface OnboardingCandidate {
  id: string
  name: string
  email: string
  phone: string
  avatar?: string
  position: string
  department: string
  manager: string
  startDate: string
  status: 'pending' | 'in_progress' | 'completed' | 'delayed'
  progress: number
  currentStep: string
  completedTasks: number
  totalTasks: number
  lastActivity: string
  hireDate: string
}

export interface OnboardingTemplate {
  id: string
  name: string
  description: string
  department: string
  duration: number
  tasks: OnboardingTask[]
  isActive: boolean
}

export interface OnboardingTask {
  id: string
  title: string
  description: string
  type: 'document' | 'meeting' | 'training' | 'system_access' | 'equipment' | 'custom'
  assignedTo: 'candidate' | 'hr' | 'manager' | 'it' | 'admin'
  dueDate: number
  priority: 'low' | 'medium' | 'high' | 'critical'
  estimatedTime: number
  dependencies?: string[]
  isCompleted: boolean
  completedDate?: string
  automationTrigger?: 'immediate' | 'previous_task' | 'specific_date'
}

export const onboardingCandidates: OnboardingCandidate[] = [
  {
    id: '1',
    name: 'Carlos Santos',
    email: 'carlos.santos@empresa.com',
    phone: '+55 11 99999-1234',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
    position: 'Frontend Developer Sênior',
    department: 'Tecnologia',
    manager: 'Ana Silva',
    startDate: '2024-02-01',
    status: 'in_progress',
    progress: 65,
    currentStep: 'Configuração de Sistemas',
    completedTasks: 13,
    totalTasks: 20,
    lastActivity: 'Há 2 horas',
    hireDate: '2024-01-15'
  },
  {
    id: '2',
    name: 'Maria Oliveira',
    email: 'maria.oliveira@empresa.com',
    phone: '+55 11 88888-5678',
    avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b95c?w=150&h=150&fit=crop&crop=face',
    position: 'UX Designer',
    department: 'Design',
    manager: 'João Costa',
    startDate: '2024-02-05',
    status: 'pending',
    progress: 0,
    currentStep: 'Aguardando Início',
    completedTasks: 0,
    totalTasks: 18,
    lastActivity: 'Pendente',
    hireDate: '2024-01-20'
  },
  {
    id: '3',
    name: 'Lucas Mendes',
    email: 'lucas.mendes@empresa.com',
    phone: '+55 21 77777-9012',
    position: 'Product Manager',
    department: 'Produto',
    manager: 'Rafael Lima',
    startDate: '2024-01-20',
    status: 'completed',
    progress: 100,
    currentStep: 'Onboarding Concluído',
    completedTasks: 22,
    totalTasks: 22,
    lastActivity: 'Há 3 dias',
    hireDate: '2024-01-05'
  },
  {
    id: '4',
    name: 'Ana Pereira',
    email: 'ana.pereira@empresa.com',
    phone: '+55 11 66666-3456',
    position: 'Data Scientist',
    department: 'Dados',
    manager: 'Pedro Santos',
    startDate: '2024-02-10',
    status: 'delayed',
    progress: 35,
    currentStep: 'Documentação Pendente',
    completedTasks: 7,
    totalTasks: 20,
    lastActivity: 'Há 5 dias',
    hireDate: '2024-01-25'
  }
]

export const onboardingTemplates: OnboardingTemplate[] = [
  {
    id: 'tech-template',
    name: 'Onboarding Tecnologia',
    description: 'Template para desenvolvedores e profissionais de TI',
    department: 'Tecnologia',
    duration: 14,
    isActive: true,
    tasks: [
      {
        id: 'welcome',
        title: 'Email de Boas-Vindas',
        description: 'Envio automático de email de boas-vindas com informações iniciais',
        type: 'document',
        assignedTo: 'hr',
        dueDate: 0,
        priority: 'high',
        estimatedTime: 5,
        isCompleted: true,
        automationTrigger: 'immediate'
      },
      {
        id: 'docs',
        title: 'Documentação Admissional',
        description: 'Envio e coleta de documentos necessários para admissão',
        type: 'document',
        assignedTo: 'candidate',
        dueDate: 2,
        priority: 'critical',
        estimatedTime: 60,
        isCompleted: false,
        automationTrigger: 'previous_task'
      },
      {
        id: 'equipment',
        title: 'Entrega de Equipamentos',
        description: 'Notebook, monitor, mouse, teclado e acessórios',
        type: 'equipment',
        assignedTo: 'it',
        dueDate: 1,
        priority: 'high',
        estimatedTime: 30,
        isCompleted: false,
        dependencies: ['docs']
      },
      {
        id: 'system_access',
        title: 'Criação de Acessos',
        description: 'Emails, sistemas internos, repositórios, ferramentas de desenvolvimento',
        type: 'system_access',
        assignedTo: 'it',
        dueDate: 1,
        priority: 'critical',
        estimatedTime: 45,
        isCompleted: false
      },
      {
        id: 'welcome_meeting',
        title: 'Reunião de Boas-Vindas',
        description: 'Apresentação da empresa, cultura e time',
        type: 'meeting',
        assignedTo: 'manager',
        dueDate: 1,
        priority: 'high',
        estimatedTime: 90,
        isCompleted: false
      }
    ]
  }
]

export function getStatusColor(status: string) {
  const colors = {
    pending: 'bg-status-warning/15 text-status-warning border-status-warning/30',
    in_progress: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default',
    completed: 'bg-status-success/15 text-status-success border-status-success/30',
    delayed: 'bg-status-error/15 text-status-error border-status-error/30'
  }
  return colors[status as keyof typeof colors] || colors.pending
}

export function getStatusLabel(status: string) {
  const labels = {
    pending: 'Pendente',
    in_progress: 'Em Andamento',
    completed: 'Concluído',
    delayed: 'Atrasado'
  }
  return labels[status as keyof typeof labels] || status
}
