export interface ApprovedCandidate {
  id: string
  name: string
  email: string
  phone: string
  avatar?: string
  position: string
  department: string
  manager: string
  hireDate: string
  startDate: string
  salary: number
  stage: 'welcome' | 'documentation' | 'equipment' | 'systems' | 'medical' | 'integration' | 'completed'
  progress: number
  tasks: OnboardingTask[]
  communications: Communication[]
  documents: OnboardingDocument[]
  medicalExams: MedicalExam[]
  firstDaySchedule?: FirstDaySchedule
}

export interface OnboardingTask {
  id: string
  title: string
  description: string
  type: 'communication' | 'document' | 'meeting' | 'system' | 'equipment' | 'medical' | 'custom'
  assignedTo: string
  dueDate: string
  isCompleted: boolean
  completedDate?: string
  automationTrigger?: string
  template?: string
}

export interface Communication {
  id: string
  type: 'email' | 'whatsapp' | 'sms' | 'call'
  templateId: string
  sentDate: string
  status: 'sent' | 'delivered' | 'read' | 'replied'
  content: string
}

export interface OnboardingDocument {
  id: string
  name: string
  type: string
  isRequired: boolean
  status: 'pending' | 'uploaded' | 'approved' | 'rejected'
  uploadDate?: string
  url?: string
}

export interface MedicalExam {
  id: string
  type: string
  provider: string
  scheduledDate?: string
  status: 'pending' | 'scheduled' | 'completed' | 'approved'
  results?: string
}

export interface FirstDaySchedule {
  date: string
  activities: {
    time: string
    activity: string
    location: string
    responsible: string
  }[]
}

export const approvedCandidates: ApprovedCandidate[] = [
  {
    id: '1',
    name: 'Carlos Santos',
    email: 'carlos.santos@empresa.com',
    phone: '+55 11 99999-1234',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
    position: 'Frontend Developer Sênior',
    department: 'Tecnologia',
    manager: 'Ana Silva',
    hireDate: '2024-01-15',
    startDate: '2024-02-01',
    salary: 13500,
    stage: 'documentation',
    progress: 35,
    tasks: [],
    communications: [],
    documents: [
      { id: '1', name: 'RG', type: 'identification', isRequired: true, status: 'uploaded' },
      { id: '2', name: 'CPF', type: 'identification', isRequired: true, status: 'approved' },
      { id: '3', name: 'Comprovante de Residência', type: 'address', isRequired: true, status: 'pending' }
    ],
    medicalExams: [
      { id: '1', type: 'Admissional', provider: 'Clínica Ocupacional SP', status: 'pending' }
    ]
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
    hireDate: '2024-01-20',
    startDate: '2024-02-05',
    salary: 9500,
    stage: 'welcome',
    progress: 15,
    tasks: [],
    communications: [],
    documents: [],
    medicalExams: []
  },
  {
    id: '3',
    name: 'Ana Pereira',
    email: 'ana.pereira@empresa.com',
    phone: '+55 11 66666-3456',
    position: 'Data Scientist',
    department: 'Dados',
    manager: 'Pedro Santos',
    hireDate: '2024-01-25',
    startDate: '2024-02-10',
    salary: 16000,
    stage: 'systems',
    progress: 70,
    tasks: [],
    communications: [],
    documents: [],
    medicalExams: [
      { id: '1', type: 'Admissional', provider: 'Clínica Ocupacional SP', status: 'completed' }
    ]
  }
]

export const kanbanStages = [
  { id: 'welcome', name: 'Boas-vindas', color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary', description: 'Email de boas-vindas enviado' },
  { id: 'documentation', name: 'Documentação', color: 'bg-status-warning/15 text-status-warning', description: 'Coleta de documentos' },
  { id: 'equipment', name: 'Equipamentos', color: 'bg-wedo-orange/15 text-wedo-orange-text', description: 'Entrega de equipamentos' },
  { id: 'systems', name: 'Sistemas', color: 'bg-wedo-purple/15 text-wedo-purple-text', description: 'Criação de acessos' },
  { id: 'medical', name: 'Médico', color: 'bg-wedo-magenta/15 text-wedo-magenta-text', description: 'Exames ocupacionais' },
  { id: 'integration', name: 'Integração', color: 'bg-wedo-purple/15 text-wedo-purple-text', description: 'Primeiro dia' },
  { id: 'completed', name: 'Concluído', color: 'bg-status-success/15 text-status-success', description: 'Onboarding finalizado' }
]

export const messageTemplates = [
  {
    id: 'welcome_email',
    name: 'Email de Boas-vindas',
    type: 'email',
    subject: 'Bem-vindo(a) à {{company_name}}! 🎉',
    content: `Olá {{candidate_name}},

É com grande prazer que damos as boas-vindas à {{company_name}}!

Estamos muito animados para tê-lo(a) em nossa equipe como {{position}} no departamento de {{department}}.

Sua jornada de onboarding começará em {{start_date}}. Nos próximos dias, você receberá informações importantes sobre:

• Documentação necessária
• Entrega de equipamentos
• Criação de acessos aos sistemas
• Exames médicos ocupacionais
• Agenda do primeiro dia

Seu gestor direto será {{manager_name}}, que entrará em contato em breve.

Estamos aqui para ajudar em qualquer dúvida!

Atenciosamente,
Equipe de RH`
  },
  {
    id: 'whatsapp_welcome',
    name: 'WhatsApp Boas-vindas',
    type: 'whatsapp',
    content: `🎉 Olá {{candidate_name}}!

Bem-vindo(a) à {{company_name}}!

Estamos muito felizes em tê-lo(a) em nossa equipe como {{position}}.

Em breve você receberá por email todas as informações sobre seu processo de onboarding.

Qualquer dúvida, estamos aqui! 😊

Equipe RH {{company_name}}`
  },
  {
    id: 'documentation_request',
    name: 'Solicitação de Documentos',
    type: 'email',
    subject: 'Documentos para Admissão - {{company_name}}',
    content: `Olá {{candidate_name}},

Para darmos continuidade ao seu processo de admissão, precisamos que você envie os seguintes documentos:

📄 DOCUMENTOS OBRIGATÓRIOS:
• RG (frente e verso)
• CPF
• Comprovante de residência (máximo 3 meses)
• Carteira de Trabalho (páginas principais)
• Título de Eleitor
• Certificado de Reservista (se aplicável)
• Diploma/Certificados de escolaridade

🏥 DOCUMENTOS MÉDICOS:
• Carteira de Vacinação atualizada
• Exames pré-admissionais (agendaremos)

📧 Envie os documentos digitalizados para: docs@{{company_name}}.com

⏰ Prazo: {{deadline}}

Em caso de dúvidas, entre em contato conosco.

Atenciosamente,
Equipe RH`
  }
]
