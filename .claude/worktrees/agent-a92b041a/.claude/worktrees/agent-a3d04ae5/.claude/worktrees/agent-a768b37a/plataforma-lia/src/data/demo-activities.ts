/**
 * Demo Activities Data - COMPLETE VERSION
 * 
 * This file contains COMPLETE example activity data for the Activities tab in the candidate preview.
 * Each activity includes full details that developers can use as reference for real layouts.
 * 
 * In production, this data should be replaced with real API data from the backend.
 * To disable demo data, set NEXT_PUBLIC_USE_DEMO_DATA=false in your environment.
 */

import {
  Mail,
  Calendar,
  Brain,
  FileText,
  Video,
  Code,
  Gift,
  ClipboardCheck,
  Mic,
} from "lucide-react"

export interface ActivityDetail {
  [key: string]: any
}

export interface Activity {
  id: string
  type: string
  icon: any
  iconColor: string
  title: string
  author: string
  date: string
  timestamp: Date
  summary: string
  jobId?: string
  jobTitle?: string
  score?: number
  statusLabel?: string
  status?: 'approved' | 'completed' | 'in-progress' | 'rejected' | 'pending'
  details?: ActivityDetail
}

export const getDemoActivities = (): Activity[] => {
  const now = Date.now()
  
  return [
    // ==========================================
    // EMAIL ENVIADO - Convite para Entrevista
    // ==========================================
    {
      id: 'act-1',
      type: 'email-sent',
      icon: Mail,
      iconColor: '#3B82F6',
      title: 'Email de convite para entrevista enviado',
      author: 'Maria Santos',
      date: 'Hoje, 10:30',
      timestamp: new Date(now - 2 * 60 * 60 * 1000),
      summary: 'Convite para entrevista técnica com time de engenharia agendada para 15/01',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      statusLabel: 'Enviado',
      status: 'completed',
      details: {
        subject: 'Convite: Entrevista Técnica - Tech Lead Mobile | WeDo Talent',
        to: 'bruno.carvalho@email.com',
        from: 'maria.santos@wedotalent.com.br',
        cc: 'recrutamento@wedotalent.com.br',
        opened: true,
        openedAt: 'Hoje às 11:45',
        clickedLinks: true,
        body: `Olá Bruno,

Esperamos que esteja bem! É com grande satisfação que entramos em contato para informar que sua candidatura para a posição de Tech Lead Mobile foi muito bem avaliada pela nossa equipe.

Gostaríamos de convidá-lo para a próxima etapa do processo seletivo: uma entrevista técnica com nosso time de engenharia.

📅 DATA E HORÁRIO
• Data: Quarta-feira, 15 de Janeiro de 2026
• Horário: 14:00 (horário de Brasília)
• Duração estimada: 60 minutos

📍 LOCAL
A entrevista será realizada via Google Meet. O link de acesso será enviado 30 minutos antes do horário agendado.

👥 PARTICIPANTES
• Carlos Mendes - Engineering Manager
• Ana Paula Silva - Senior Mobile Developer

📋 O QUE SERÁ AVALIADO
• Arquitetura de aplicações mobile
• Experiência com React Native
• Liderança técnica e gestão de equipes
• Práticas de CI/CD e qualidade de código

Por favor, confirme sua disponibilidade respondendo este email até 13/01/2026.

Caso tenha algum impedimento no horário proposto, podemos reagendar. Basta nos informar suas preferências.

Estamos muito animados com a possibilidade de tê-lo em nossa equipe!

Atenciosamente,

Maria Santos
Talent Acquisition Lead
WeDo Talent
📞 (11) 99999-8888
📧 maria.santos@wedotalent.com.br`,
        attachments: ['Descrição da Vaga - Tech Lead Mobile.pdf', 'Sobre a Empresa.pdf'],
        suggestedTimes: ['15/01 às 14:00', '16/01 às 10:00', '16/01 às 15:00'],
        template: 'convite_entrevista_tecnica'
      }
    },

    // ==========================================
    // ENTREVISTA AGENDADA
    // ==========================================
    {
      id: 'act-2',
      type: 'interview-scheduled',
      icon: Calendar,
      iconColor: '#8B5CF6',
      title: 'Entrevista técnica agendada',
      author: 'Sistema',
      date: 'Hoje, 09:15',
      timestamp: new Date(now - 4 * 60 * 60 * 1000),
      summary: 'Entrevista com Time de Engenharia marcada para 15/01 às 14:00',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      statusLabel: 'Confirmada',
      status: 'approved',
      details: {
        interviewType: 'Entrevista Técnica',
        stage: '3ª Etapa - Avaliação Técnica',
        dateTime: '15/01/2026 às 14:00',
        endTime: '15:00',
        duration: '60 minutos',
        timezone: 'America/Sao_Paulo (GMT-3)',
        location: 'Google Meet',
        meetLink: 'https://meet.google.com/abc-defg-hij',
        calendarEventId: 'evt_abc123xyz',
        interviewers: [
          { name: 'Carlos Mendes', role: 'Engineering Manager', email: 'carlos.mendes@empresa.com.br', photo: null },
          { name: 'Ana Paula Silva', role: 'Senior Mobile Developer', email: 'ana.paula@empresa.com.br', photo: null }
        ],
        topics: [
          'Arquitetura de Aplicações Mobile',
          'React Native - Performance e Otimização',
          'Liderança Técnica e Gestão de Equipes',
          'CI/CD e DevOps Mobile',
          'Case Técnico: Design de Sistema'
        ],
        preparation: [
          'Revisar arquitetura de micro-frontends',
          'Preparar case sobre escalabilidade',
          'Ter exemplos de liderança técnica'
        ],
        candidateConfirmed: true,
        confirmedAt: 'Hoje às 11:50',
        reminderSent: false,
        reminderScheduled: '15/01/2026 às 13:30',
        notes: 'Candidato confirmou participação via email. Demonstrou interesse em discutir arquitetura de sistemas distribuídos.',
        previousInterviews: [
          { stage: '1ª Etapa', type: 'Triagem LIA', date: '08/01/2026', result: 'Aprovado', score: 91 },
          { stage: '2ª Etapa', type: 'Triagem por Voz', date: '10/01/2026', result: 'Aprovado', score: 93 }
        ]
      }
    },

    // ==========================================
    // AVALIAÇÃO LIA (IA)
    // ==========================================
    {
      id: 'act-3',
      type: 'lia-evaluation',
      icon: Brain,
      iconColor: '#60BED1',
      title: 'Avaliação automática da LIA concluída',
      author: 'LIA',
      date: 'Ontem, 16:45',
      timestamp: new Date(now - 20 * 60 * 60 * 1000),
      summary: 'Análise de CV e perfil LinkedIn realizada com score de 91%',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      score: 91,
      statusLabel: 'Altamente Recomendado',
      status: 'approved',
      details: {
        technicalScore: 94,
        culturalFit: 88,
        experience: 92,
        softSkills: 89,
        overallScore: 91,
        analysisTime: '2.3 segundos',
        dataSourcesUsed: ['CV Anexado', 'LinkedIn', 'GitHub'],
        strengths: [
          'Domínio avançado de React Native (5+ anos)',
          'Experiência comprovada em liderança de equipes (4 anos)',
          'Histórico de entregas em grandes empresas (Nubank, iFood)',
          'Contribuições open source relevantes',
          'Certificações AWS e Google Cloud'
        ],
        areasToImprove: [
          'Experiência limitada com Flutter',
          'Sem certificações específicas de segurança mobile',
          'Poderia ter mais experiência com Kotlin nativo'
        ],
        keyHighlights: [
          { label: 'Tempo de Experiência', value: '8 anos em mobile' },
          { label: 'Maior Equipe Liderada', value: '12 desenvolvedores' },
          { label: 'Maior App Entregue', value: '5M+ downloads' },
          { label: 'Contribuições Open Source', value: '47 PRs aceitos' }
        ],
        recommendation: 'Candidato altamente qualificado para a posição de Tech Lead Mobile. Possui experiência sólida em liderança técnica, domínio comprovado de React Native e histórico de entregas em empresas de grande porte. Sua experiência com arquitetura de sistemas distribuídos e práticas de DevOps é um diferencial significativo.\n\nRecomendo fortemente agendar entrevista técnica com foco em:\n1. Arquitetura de sistemas mobile escaláveis\n2. Gestão de equipes multidisciplinares\n3. Estratégias de migração e modernização de apps',
        comparisonToPool: {
          percentile: 95,
          totalCandidates: 47,
          ranking: 3
        }
      }
    },

    // ==========================================
    // CANDIDATURA RECEBIDA
    // ==========================================
    {
      id: 'act-4',
      type: 'job-application',
      icon: FileText,
      iconColor: '#10B981',
      title: 'Candidatura recebida via LinkedIn',
      author: 'Sistema',
      date: 'Ontem, 14:20',
      timestamp: new Date(now - 22 * 60 * 60 * 1000),
      summary: 'Candidato aplicou para a vaga de Tech Lead Mobile através da integração com LinkedIn',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      statusLabel: 'Nova',
      status: 'completed',
      details: {
        source: 'LinkedIn Jobs',
        sourceIcon: 'linkedin',
        applicationMethod: 'Easy Apply',
        applicationId: 'APP-2026-001234',
        receivedAt: '13/01/2026 às 14:20:33',
        ipLocation: 'São Paulo, SP, Brasil',
        device: 'iPhone 15 Pro - LinkedIn App',
        resumeAttached: true,
        resumeFileName: 'Bruno_Carvalho_CV_2026.pdf',
        resumeSize: '245 KB',
        coverLetter: true,
        coverLetterPreview: 'Prezados, é com grande entusiasmo que me candidato à posição de Tech Lead Mobile. Com mais de 8 anos de experiência em desenvolvimento mobile e 4 anos liderando equipes...',
        linkedinUrl: 'https://linkedin.com/in/brunocarvalho',
        portfolioUrl: 'https://github.com/brunocarvalho',
        screeningQuestions: [
          { 
            question: 'Quantos anos de experiência você tem com React Native?', 
            answer: '5 anos de experiência profissional, sendo 3 anos como lead de projetos.',
            isRequired: true,
            isQualifying: true,
            passed: true
          },
          { 
            question: 'Você tem experiência liderando equipes de desenvolvimento?', 
            answer: 'Sim, liderei equipes de 4 a 12 desenvolvedores em 3 empresas diferentes.',
            isRequired: true,
            isQualifying: true,
            passed: true
          },
          { 
            question: 'Qual sua pretensão salarial?', 
            answer: 'Entre R$ 25.000 e R$ 30.000 CLT',
            isRequired: true,
            isQualifying: false,
            passed: true
          },
          { 
            question: 'Você tem disponibilidade para trabalho híbrido em São Paulo?', 
            answer: 'Sim, disponível para modelo híbrido (3x presencial).',
            isRequired: true,
            isQualifying: true,
            passed: true
          }
        ],
        tags: ['React Native', 'Tech Lead', 'Mobile', 'São Paulo'],
        autoScreeningResult: 'Passou em todos os critérios eliminatórios',
        assignedTo: 'Maria Santos',
        assignedAt: '13/01/2026 às 14:25'
      }
    },

    // ==========================================
    // TRIAGEM POR VOZ (VOICE SCREENING)
    // ==========================================
    {
      id: 'act-5',
      type: 'voice-screening',
      icon: Mic,
      iconColor: '#EF4444',
      title: 'Triagem por voz concluída',
      author: 'LIA',
      date: '2 dias atrás, 11:00',
      timestamp: new Date(now - 2 * 24 * 60 * 60 * 1000),
      summary: 'Candidato completou triagem de voz com 4 perguntas respondidas',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      score: 93,
      statusLabel: 'Concluída',
      status: 'completed',
      details: {
        duration: '4:32',
        durationSeconds: 272,
        questionsAnswered: 4,
        totalQuestions: 4,
        completionRate: 100,
        transcriptionAvailable: true,
        audioUrl: '/api/v1/audio/screening-bruno-001.mp3',
        language: 'pt-BR',
        transcriptionEngine: 'Deepgram Nova-2',
        transcriptionConfidence: 0.97,
        wsiScore: {
          technicalWsi: 4.3,
          behavioralWsi: 4.1,
          overallWsi: 4.2,
          classification: 'alto',
          percentile: 87
        },
        liaParecer: {
          pontosFortes: 'Excelente domínio técnico em React Native com 8+ anos de experiência. Liderança comprovada de equipes de até 12 desenvolvedores. Experiência em projetos de grande escala (5M+ usuários). Comunicação clara e objetiva durante toda a triagem.',
          pontosAtencao: 'Pretensão salarial no topo da faixa prevista. Experiência limitada com Flutter, caso seja necessário migração futura.',
          recomendacao: 'Fortemente recomendado para próxima etapa. O candidato demonstra senioridade técnica e comportamental compatível com a posição de Tech Lead. Sugerimos entrevista técnica focada em arquitetura de sistemas distribuídos.',
          scoreGeral: 93,
          classificacao: 'Altamente Recomendado'
        },
        aiAnalysis: {
          clarity: 94,
          confidence: 91,
          technicalKnowledge: 96,
          communication: 89,
          enthusiasm: 87,
          professionalism: 92
        },
        questions: [
          {
            id: 1,
            question: 'Conte-nos sobre sua experiência com desenvolvimento mobile e liderança de equipes.',
            duration: '1:15',
            transcription: 'Olá! Trabalho com desenvolvimento mobile há mais de 8 anos, começando com Android nativo e depois migrando para React Native. Nos últimos 4 anos, tenho liderado equipes de desenvolvimento, atualmente gerenciando um time de 6 desenvolvedores no Nubank. Minha principal responsabilidade é definir a arquitetura técnica dos nossos apps e garantir a qualidade das entregas...',
            analysis: {
              sentiment: 'positive',
              keywords: ['React Native', 'liderança', 'arquitetura', 'Nubank'],
              score: 95
            }
          },
          {
            id: 2,
            question: 'Qual foi o maior desafio técnico que você enfrentou e como resolveu?',
            duration: '1:28',
            transcription: 'O maior desafio foi a migração de um app com 5 milhões de usuários ativos de uma arquitetura monolítica para micro-frontends. Precisamos fazer isso sem interromper o serviço e mantendo a performance. Implementamos feature flags, testes A/B e uma estratégia de rollout gradual que permitiu validar cada mudança com um grupo pequeno de usuários antes de expandir...',
            analysis: {
              sentiment: 'positive',
              keywords: ['migração', 'micro-frontends', 'feature flags', '5 milhões'],
              score: 97
            }
          },
          {
            id: 3,
            question: 'Como você lida com conflitos dentro da equipe técnica?',
            duration: '0:58',
            transcription: 'Acredito muito em comunicação transparente e em criar um ambiente seguro para discussões técnicas. Quando há conflitos, primeiro ouço todas as partes envolvidas separadamente, depois facilito uma discussão em grupo focada em dados e resultados, não em opiniões pessoais. Usamos ADRs para documentar decisões importantes...',
            analysis: {
              sentiment: 'positive',
              keywords: ['comunicação', 'ambiente seguro', 'ADRs', 'dados'],
              score: 89
            }
          },
          {
            id: 4,
            question: 'Qual sua disponibilidade e pretensão salarial?',
            duration: '0:51',
            transcription: 'Tenho disponibilidade imediata, posso iniciar com aviso prévio de 30 dias caso seja necessário. Minha pretensão salarial está na faixa de 28 a 32 mil reais em regime CLT, considerando o pacote de benefícios. Estou aberto a negociação dependendo do escopo da posição e oportunidades de crescimento...',
            analysis: {
              sentiment: 'neutral',
              keywords: ['disponibilidade imediata', '28-32k', 'CLT', 'negociação'],
              score: 85
            }
          }
        ],
        highlights: [
          '8+ anos de experiência em desenvolvimento mobile',
          'Liderou time de 6 desenvolvedores no Nubank',
          'Migrou app com 5M+ usuários para micro-frontends',
          'Disponibilidade imediata (aviso prévio 30 dias)',
          'Pretensão salarial: R$ 28-32k CLT'
        ],
        redFlags: [],
        overallImpression: 'Candidato demonstrou excelente comunicação, conhecimento técnico profundo e experiência relevante em liderança. Respostas claras e objetivas, com exemplos concretos de situações reais.',
        nextSteps: 'Recomendado para entrevista técnica com time de engenharia.'
      }
    },

    // ==========================================
    // TESTE TÉCNICO CONCLUÍDO
    // ==========================================
    {
      id: 'act-6',
      type: 'test-completed',
      icon: Code,
      iconColor: '#F59E0B',
      title: 'Teste técnico concluído',
      author: 'Sistema',
      date: '3 dias atrás, 18:30',
      timestamp: new Date(now - 3 * 24 * 60 * 60 * 1000),
      summary: 'Candidato finalizou teste de React Native com aproveitamento de 87%',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      score: 87,
      statusLabel: 'Aprovado',
      status: 'approved',
      details: {
        testName: 'React Native - Nível Sênior',
        testType: 'Técnico',
        testId: 'TEST-RN-SR-001',
        provider: 'HackerRank',
        duration: '45 minutos',
        timeSpent: '38 minutos',
        startedAt: '10/01/2026 às 17:52',
        completedAt: '10/01/2026 às 18:30',
        totalQuestions: 20,
        correctAnswers: 17,
        wrongAnswers: 2,
        skippedAnswers: 1,
        maxScore: 100,
        passingScore: 70,
        categories: [
          { name: 'Fundamentos React Native', questions: 5, correct: 5, score: 100 },
          { name: 'State Management (Redux/Context)', questions: 4, correct: 3, score: 75 },
          { name: 'Performance & Otimização', questions: 4, correct: 4, score: 100 },
          { name: 'Navegação & Routing', questions: 3, correct: 3, score: 100 },
          { name: 'Testing (Jest/Detox)', questions: 4, correct: 2, score: 50 }
        ],
        questionsBreakdown: [
          { id: 1, topic: 'Hooks', difficulty: 'Medium', correct: true, timeSpent: '1:20' },
          { id: 2, topic: 'Redux Thunk', difficulty: 'Hard', correct: true, timeSpent: '2:45' },
          { id: 3, topic: 'FlatList Optimization', difficulty: 'Hard', correct: true, timeSpent: '3:10' },
          { id: 4, topic: 'Native Modules', difficulty: 'Hard', correct: false, timeSpent: '4:00' },
          { id: 5, topic: 'Detox E2E', difficulty: 'Medium', correct: false, timeSpent: '2:30' }
        ],
        ranking: 'Top 15% dos candidatos',
        percentile: 85,
        totalCandidatesForTest: 234,
        codeChallenge: {
          name: 'Implementar Lista Infinita com Cache',
          submitted: true,
          codeQuality: 88,
          functionality: 92,
          bestPractices: 85,
          feedback: 'Código bem estruturado e funcional. Sugestão: adicionar tratamento de erro mais robusto.'
        },
        proctoring: {
          enabled: true,
          flagsDetected: 0,
          tabSwitches: 2,
          copyPasteEvents: 0,
          status: 'Clean'
        },
        certificateUrl: '/api/v1/certificates/test-rn-bruno-001.pdf',
        retakeAllowed: false,
        validUntil: '10/01/2027'
      }
    },

    // ==========================================
    // PROPOSTA SALARIAL ENVIADA
    // ==========================================
    {
      id: 'act-7',
      type: 'offer-sent',
      icon: Gift,
      iconColor: '#06B6D4',
      title: 'Proposta salarial enviada',
      author: 'João Silva (HR)',
      date: '1 semana atrás',
      timestamp: new Date(now - 7 * 24 * 60 * 60 * 1000),
      summary: 'Proposta formal enviada com pacote de benefícios completo',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      statusLabel: 'Aguardando Resposta',
      status: 'in-progress',
      details: {
        offerNumber: 'OFF-2026-000123',
        offerDate: '06/01/2026',
        validUntil: '20/01/2026',
        daysRemaining: 7,
        salary: 'R$ 28.000,00',
        salaryType: 'CLT',
        annualBonus: 'Até 3 salários (performance)',
        stockOptions: '1.000 opções (vesting 4 anos)',
        signingBonus: 'R$ 10.000,00',
        benefits: [
          { name: 'Vale Refeição', value: 'R$ 1.200/mês', icon: '🍽️' },
          { name: 'Vale Alimentação', value: 'R$ 800/mês', icon: '🛒' },
          { name: 'Plano de Saúde', value: 'Bradesco Top Nacional', icon: '🏥' },
          { name: 'Plano Odontológico', value: 'Odontoprev', icon: '🦷' },
          { name: 'Seguro de Vida', value: '24x salário', icon: '🛡️' },
          { name: 'PLR', value: 'Até 2 salários/ano', icon: '💰' },
          { name: 'Home Office', value: 'Híbrido (2x escritório)', icon: '🏠' },
          { name: 'Gympass', value: 'Plano Gold', icon: '💪' },
          { name: 'Auxílio Home Office', value: 'R$ 200/mês', icon: '💻' },
          { name: 'Day Off Aniversário', value: 'Folga no aniversário', icon: '🎂' },
          { name: 'Buddy Days', value: '2 dias/mês flexíveis', icon: '📅' }
        ],
        startDate: '01/02/2026',
        contractType: 'CLT - Tempo Indeterminado',
        workLocation: 'São Paulo, SP - Vila Olímpia',
        workModel: 'Híbrido (3x presencial, 2x remoto)',
        reportingTo: 'Carlos Mendes - VP de Engenharia',
        teamSize: '8-12 desenvolvedores',
        probationPeriod: '90 dias',
        negotiationHistory: [
          { date: '05/01/2026', action: 'Proposta inicial enviada', salary: 'R$ 26.000', status: 'Recusada' },
          { date: '06/01/2026', action: 'Contraproposta recebida', salary: 'R$ 30.000', status: 'Analisando' },
          { date: '06/01/2026', action: 'Proposta revisada enviada', salary: 'R$ 28.000', status: 'Aguardando' }
        ],
        negotiationNotes: 'Candidato solicitou revisão do valor de VR (de R$1.000 para R$1.200) e possibilidade de 100% remoto após período de experiência. VR foi ajustado. Modelo 100% remoto negado, mas oferecemos 2x presencial após 6 meses.',
        documentsToSign: [
          'Contrato de Trabalho',
          'Termo de Confidencialidade (NDA)',
          'Política de Propriedade Intelectual',
          'Acordo de Home Office'
        ],
        sentVia: 'Email + DocuSign',
        viewedAt: '06/01/2026 às 19:30',
        lastInteraction: '08/01/2026 - Candidato solicitou tempo para análise'
      }
    },

    // ==========================================
    // AVALIAÇÃO POR RUBRICA (CV vs VAGA)
    // ==========================================
    {
      id: 'act-8',
      type: 'rubric_evaluation',
      icon: ClipboardCheck,
      iconColor: '#60BED1',
      title: 'Avaliação por Rubrica (CV vs Vaga)',
      author: 'LIA',
      date: '4 dias atrás, 09:00',
      timestamp: new Date(now - 4 * 24 * 60 * 60 * 1000),
      summary: 'Análise detalhada de aderência do CV aos requisitos da vaga',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      score: 89,
      statusLabel: 'Fit Alto',
      status: 'approved',
      details: {
        overallFit: 89,
        evaluationType: 'Automática + Revisão Manual',
        evaluatedBy: 'LIA + Maria Santos',
        evaluatedAt: '09/01/2026 às 09:00',
        methodVersion: 'WSI v2.3',
        totalCriteria: 5,
        criteriaScores: [
          { 
            criteria: 'Experiência com React Native', 
            weight: 25, 
            score: 95, 
            maxScore: 100,
            notes: 'Supera requisitos mínimos: 5 anos de experiência vs 3 anos exigidos',
            evidence: 'CV indica 5 anos de experiência profissional com React Native, incluindo projetos de grande escala no Nubank e iFood.',
            status: 'exceeded'
          },
          { 
            criteria: 'Liderança Técnica', 
            weight: 20, 
            score: 90, 
            maxScore: 100,
            notes: '4 anos liderando equipes de 4-12 desenvolvedores',
            evidence: 'Histórico de liderança em 3 empresas diferentes, com progressão clara de responsabilidades.',
            status: 'met'
          },
          { 
            criteria: 'Formação Acadêmica', 
            weight: 15, 
            score: 85, 
            maxScore: 100,
            notes: 'Ciência da Computação - USP (requisito: graduação em TI)',
            evidence: 'Bacharelado em Ciência da Computação pela USP, uma das melhores universidades do país.',
            status: 'met'
          },
          { 
            criteria: 'Inglês Avançado', 
            weight: 15, 
            score: 80, 
            maxScore: 100,
            notes: 'Fluente em conversação, precisa validar escrita técnica',
            evidence: 'CV indica nível avançado. Perfil LinkedIn em inglês. Recomenda-se teste de proficiência.',
            status: 'partial'
          },
          { 
            criteria: 'Arquitetura Mobile', 
            weight: 25, 
            score: 92, 
            maxScore: 100,
            notes: 'Experiência comprovada em projetos de larga escala',
            evidence: 'Migração de app com 5M+ usuários, implementação de micro-frontends, expertise em performance.',
            status: 'exceeded'
          }
        ],
        mustHaveRequirements: [
          { requirement: 'React Native 3+ anos', met: true, evidence: '5 anos de experiência' },
          { requirement: 'Liderança de equipes', met: true, evidence: '4 anos como tech lead' },
          { requirement: 'Graduação em TI', met: true, evidence: 'Bacharel em CC - USP' }
        ],
        niceToHaveRequirements: [
          { requirement: 'Experiência com Flutter', met: false, evidence: 'Não mencionado no CV' },
          { requirement: 'Certificação AWS', met: true, evidence: 'AWS Solutions Architect Associate' },
          { requirement: 'Contribuições open source', met: true, evidence: '47 PRs aceitos no GitHub' }
        ],
        recommendation: 'Alta aderência aos requisitos. Candidato excede expectativas em experiência técnica com React Native e arquitetura mobile. Possui todas as competências obrigatórias e a maioria das desejáveis. Recomendo priorizar para próxima fase do processo.',
        gaps: [
          'Experiência com Flutter (desejável, não obrigatório)',
          'Validar proficiência escrita em inglês'
        ],
        competitiveAdvantages: [
          'Experiência em empresas de referência (Nubank, iFood)',
          'Histórico de projetos de grande escala (5M+ usuários)',
          'Combinação rara de skills técnicos e de liderança'
        ],
        comparedToCandidates: {
          totalInPool: 47,
          ranking: 3,
          percentile: 94,
          averageScore: 72
        }
      }
    },

    // ==========================================
    // EMAIL VISUALIZADO (FOLLOW-UP)
    // ==========================================
    {
      id: 'act-9',
      type: 'email-sent',
      icon: Mail,
      iconColor: '#6366F1',
      title: 'Email de follow-up visualizado',
      author: 'Maria Santos',
      date: '5 dias atrás, 14:22',
      timestamp: new Date(now - 5 * 24 * 60 * 60 * 1000),
      summary: 'Candidato abriu email de acompanhamento do processo seletivo',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      statusLabel: 'Visualizado',
      status: 'completed',
      details: {
        subject: 'Atualização: Seu processo seletivo - Tech Lead Mobile',
        to: 'bruno.carvalho@email.com',
        from: 'maria.santos@wedotalent.com.br',
        opened: true,
        openedAt: '08/01/2026 às 14:22',
        openCount: 3,
        lastOpenedAt: '09/01/2026 às 10:15',
        device: 'iPhone 15 Pro',
        location: 'São Paulo, SP',
        clickedLinks: ['Detalhes da vaga', 'Política de benefícios', 'Sobre a empresa'],
        body: `Olá Bruno,

Gostaríamos de atualizá-lo sobre o andamento do seu processo seletivo para a posição de Tech Lead Mobile.

📋 STATUS ATUAL
Você completou com sucesso as seguintes etapas:
✓ Triagem inicial por IA
✓ Triagem por voz
✓ Teste técnico de React Native

🎯 PRÓXIMOS PASSOS
Você foi aprovado para a etapa de entrevista técnica! Em breve, nossa equipe entrará em contato para agendar um horário.

📚 ENQUANTO ISSO...
Separamos alguns materiais que podem ser úteis para você se preparar:
• Nossa cultura e valores
• Stack tecnológica da empresa
• Depoimentos do time de engenharia

Ficamos muito impressionados com seu desempenho até aqui. Seu teste técnico ficou entre os 15% melhores resultados!

Qualquer dúvida, estamos à disposição.

Atenciosamente,

Maria Santos
Talent Acquisition Lead
WeDo Talent`,
        trackingData: {
          deliveredAt: '08/01/2026 às 10:00',
          firstOpenAt: '08/01/2026 às 14:22',
          avgTimeReading: '2 min 15 seg'
        }
      }
    },

    // ==========================================
    // ASSESSMENT COMPORTAMENTAL (DISC)
    // ==========================================
    {
      id: 'act-10',
      type: 'assessment',
      icon: Brain,
      iconColor: '#EC4899',
      title: 'Assessment comportamental realizado',
      author: 'Sistema',
      date: '6 dias atrás, 16:00',
      timestamp: new Date(now - 6 * 24 * 60 * 60 * 1000),
      summary: 'Análise de perfil DISC e competências comportamentais',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      score: 85,
      statusLabel: 'Compatível',
      status: 'approved',
      details: {
        assessmentType: 'DISC + Competências Comportamentais',
        assessmentProvider: 'Thomas International',
        completedAt: '07/01/2026 às 16:00',
        duration: '25 minutos',
        questionsAnswered: 48,
        profile: 'DI - Dominância + Influência',
        profileDescription: 'Perfil orientado a resultados com forte capacidade de comunicação e influência. Tende a ser direto, competitivo e focado em objetivos.',
        primaryTraits: [
          { trait: 'Liderança Natural', score: 92, description: 'Alta capacidade de assumir controle e direcionar equipes' },
          { trait: 'Orientação a Resultados', score: 89, description: 'Foco consistente em entregas e metas' },
          { trait: 'Comunicação', score: 85, description: 'Habilidade de articular ideias e influenciar stakeholders' },
          { trait: 'Pensamento Analítico', score: 78, description: 'Capacidade de análise e resolução de problemas' }
        ],
        discScores: {
          dominance: 85,
          influence: 78,
          steadiness: 45,
          conscientiousness: 68
        },
        culturalFitScore: 88,
        culturalFitDetails: [
          { dimension: 'Inovação', companyValue: 90, candidateValue: 85, fit: 'Alto' },
          { dimension: 'Colaboração', companyValue: 85, candidateValue: 80, fit: 'Alto' },
          { dimension: 'Agilidade', companyValue: 80, candidateValue: 88, fit: 'Alto' },
          { dimension: 'Autonomia', companyValue: 75, candidateValue: 90, fit: 'Médio' }
        ],
        leadershipScore: 91,
        leadershipStyle: 'Transformacional',
        leadershipStrengths: [
          'Visão estratégica clara',
          'Capacidade de inspirar e motivar equipes',
          'Tomada de decisão assertiva',
          'Orientação para desenvolvimento de talentos'
        ],
        teamworkScore: 84,
        adaptabilityScore: 79,
        stressResilienceScore: 82,
        developmentAreas: [
          'Paciência com processos mais lentos',
          'Delegação efetiva (tendência a assumir demais)',
          'Escuta ativa em situações de conflito'
        ],
        recommendation: 'Perfil altamente compatível com a posição de Tech Lead Mobile. O candidato apresenta características de liderança transformacional, o que é ideal para a cultura de inovação da empresa. Sua orientação a resultados e capacidade de comunicação são pontos fortes significativos para gestão de equipes técnicas.',
        comparisonToRole: {
          idealProfile: 'DI ou DC',
          candidateProfile: 'DI',
          matchPercentage: 92
        },
        reportUrl: '/api/v1/assessments/disc-bruno-001.pdf'
      }
    },

    // ==========================================
    // ENTREVISTA EM VÍDEO (VIDEO INTERVIEW)
    // ==========================================
    {
      id: 'act-11',
      type: 'video-interview',
      icon: Video,
      iconColor: '#8B5CF6',
      title: 'Entrevista em vídeo concluída',
      author: 'LIA',
      date: '1 dia atrás, 15:30',
      timestamp: new Date(now - 1 * 24 * 60 * 60 * 1000),
      summary: 'Candidato completou entrevista em vídeo com 5 perguntas respondidas',
      jobId: 'job-001',
      jobTitle: 'Tech Lead Mobile',
      score: 91,
      statusLabel: 'Concluída',
      status: 'completed',
      details: {
        duration: '8:45',
        durationSeconds: 525,
        questionsAnswered: 5,
        totalQuestions: 5,
        completionRate: 100,
        transcriptionAvailable: true,
        videoUrl: '/api/v1/video/interview-bruno-001.mp4',
        language: 'pt-BR',
        transcriptionEngine: 'Deepgram Nova-2',
        transcriptionConfidence: 0.95,
        wsiScore: {
          technicalWsi: 4.5,
          behavioralWsi: 4.2,
          overallWsi: 4.4,
          classification: 'excelente',
          percentile: 92
        },
        liaParecer: {
          pontosFortes: 'Comunicação visual excelente, manteve contato visual e postura profissional. Demonstrou clareza nas explicações técnicas com exemplos práticos. Excelente articulação de ideias complexas.',
          pontosAtencao: 'Em alguns momentos, as respostas foram um pouco longas. Poderia ser mais conciso em explicações técnicas.',
          recomendacao: 'Candidato demonstra senioridade e presença executiva. Recomendado fortemente para entrevista final com stakeholders. Perfil ideal para posição de liderança.',
          scoreGeral: 91,
          classificacao: 'Altamente Recomendado'
        },
        aiAnalysis: {
          clarity: 92,
          confidence: 94,
          technicalKnowledge: 95,
          communication: 91,
          enthusiasm: 88,
          professionalism: 96
        },
        questions: [
          {
            id: 1,
            question: 'Descreva uma situação onde você precisou tomar uma decisão técnica difícil sob pressão.',
            duration: '1:45',
            timestamp: '0:00',
            transcription: 'Recentemente, enfrentamos uma situação crítica onde nosso app principal teve uma degradação de performance que afetava 30% dos usuários. Precisávamos decidir entre um hotfix rápido ou uma solução mais robusta. Optei por implementar um feature flag que nos permitiu fazer um rollout gradual da correção, mantendo a estabilidade...',
            analysis: {
              sentiment: 'positive',
              keywords: ['decisão técnica', 'pressão', 'feature flag', 'rollout gradual'],
              score: 94
            }
          },
          {
            id: 2,
            question: 'Como você gerencia e desenvolve talentos em sua equipe?',
            duration: '2:10',
            timestamp: '1:45',
            transcription: 'Acredito muito em criar um ambiente de aprendizado contínuo. Implementei 1:1s semanais com cada membro da equipe, onde discutimos não só entregas mas também carreira e desenvolvimento pessoal. Criei um programa de mentoria interna onde desenvolvedores mais experientes ajudam os mais juniores...',
            analysis: {
              sentiment: 'positive',
              keywords: ['desenvolvimento de talentos', '1:1s', 'mentoria', 'aprendizado contínuo'],
              score: 93
            }
          },
          {
            id: 3,
            question: 'Qual é sua abordagem para garantir qualidade de código em times grandes?',
            duration: '1:55',
            timestamp: '3:55',
            transcription: 'Implemento uma cultura de code review rigorosa onde todo código passa por pelo menos dois revisores. Utilizamos testes automatizados com cobertura mínima de 80%. Temos ADRs para documentar decisões arquiteturais importantes. Também fazemos pair programming em features críticas...',
            analysis: {
              sentiment: 'positive',
              keywords: ['code review', 'testes automatizados', 'ADRs', 'pair programming'],
              score: 96
            }
          },
          {
            id: 4,
            question: 'Como você lida com stakeholders não-técnicos?',
            duration: '1:30',
            timestamp: '5:50',
            transcription: 'Aprendi a adaptar minha comunicação dependendo do público. Com stakeholders não-técnicos, foco em resultados de negócio e impacto para o usuário. Uso analogias simples para explicar conceitos técnicos. Sempre trago métricas e dados que demonstram o valor das iniciativas técnicas...',
            analysis: {
              sentiment: 'positive',
              keywords: ['comunicação', 'stakeholders', 'métricas', 'resultados de negócio'],
              score: 89
            }
          },
          {
            id: 5,
            question: 'Onde você se vê em 3-5 anos?',
            duration: '1:25',
            timestamp: '7:20',
            transcription: 'Meu objetivo é evoluir para uma posição de VP ou Head de Engenharia, onde posso ter maior impacto estratégico. Quero continuar construindo times de alta performance e contribuindo para decisões de produto. Também tenho interesse em mentoria de líderes técnicos mais juniores...',
            analysis: {
              sentiment: 'positive',
              keywords: ['VP de Engenharia', 'estratégico', 'alta performance', 'mentoria'],
              score: 87
            }
          }
        ],
        highlights: [
          'Excelente presença executiva e comunicação visual',
          'Experiência comprovada em gestão de crises técnicas',
          'Forte foco em desenvolvimento de talentos',
          'Abordagem estruturada para qualidade de código',
          'Ambição saudável de crescimento na carreira'
        ],
        redFlags: [],
        overallImpression: 'Candidato demonstrou excelente postura profissional, conhecimento técnico avançado e habilidades de liderança maduras. Comunicação clara e objetiva com exemplos concretos em todas as respostas.',
        nextSteps: 'Recomendado para entrevista final com VP de Engenharia e stakeholders de produto.'
      }
    }
  ]
}
