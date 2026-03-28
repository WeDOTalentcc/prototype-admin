import type { WizardPhaseConfig, WizardStageConfig, WizardStage } from './types'
import type { JobBenefit } from '@/types/benefits'

export const WIZARD_PHASES: WizardPhaseConfig[] = [
  { id: 'construction', label: 'Construção', stages: ['input-evaluation', 'job-description', 'competencies', 'salary', 'wsi-questions'] },
  { id: 'activation', label: 'Ativação', stages: ['review-publish'] },
  { id: 'selection', label: 'Seleção', stages: ['search-calibration'] }
]

export const WIZARD_STAGES: WizardStageConfig[] = [
  {
    id: 'input-evaluation',
    title: 'Avaliação',
    subtitle: 'Construção',
    panelTitle: 'Critérios Detectados',
    liaMessage: `Olá! Vou te ajudar a criar uma nova vaga.

**Envie sua descrição** e eu vou analisar proativamente o conteúdo para:
- Extrair cargo, senioridade e responsabilidades
- Identificar competências técnicas e comportamentais
- Sugerir faixa salarial baseada em benchmarks de mercado
- Preencher campos operacionais com base no setup da empresa

Quanto mais detalhes você fornecer, mais completa será a análise!

Digite sua descrição ou anexe um JD existente para começarmos.`
  },
  {
    id: 'job-description',
    title: 'Descrição da Vaga',
    subtitle: 'Construção',
    panelTitle: 'Informações da Vaga',
    liaMessage: `Análise concluída! Preenchi os campos com base na sua descrição e no setup da empresa.

No painel ao lado você encontra:
- **Informações básicas**: cargo, área, gestor, localidade
- **Modelo de trabalho**: remoto, híbrido ou presencial
- **Tipo de contrato**: CLT, PJ, temporário

Revise e ajuste conforme necessário. Se precisar alterar algo, é só me dizer ou editar diretamente!`
  },
  {
    id: 'competencies',
    title: 'Competências',
    subtitle: 'Construção',
    panelTitle: 'Competências da Vaga',
    liaMessage: `Agora vamos definir as competências da vaga!

No painel ao lado você encontra:
- **Competências Técnicas**: Conhecimentos e ferramentas da área
- **Competências Comportamentais**: Soft skills e fit cultural

Para cada competência você pode:
- Ajustar o nível de proficiência
- Definir peso (1-5 estrelas) para impacto na Nota LIA
- Marcar como obrigatório ou desejável

Edite diretamente no painel ao lado.`
  },
  {
    id: 'salary',
    title: 'Remuneração',
    subtitle: 'Construção',
    panelTitle: 'Salário e Benefícios',
    liaMessage: `Ótimo progresso! Agora vamos para remuneração e benefícios.

Com base nas informações da empresa e conforme nível/área da posição, os benefícios e faixas salariais foram sugeridos. Defina:
- Faixa salarial (mínimo e máximo)
- Bônus anual e critérios
- Benefícios oferecidos

Esses dados ajudam a atrair candidatos qualificados.`
  },
  {
    id: 'wsi-questions',
    title: 'Triagem WSI',
    subtitle: 'Construção',
    panelTitle: 'Perguntas de Triagem WSI',
    liaMessage: `Quase lá! Agora vamos configurar as perguntas de triagem rápida.

Essas perguntas serão enviadas automaticamente via WhatsApp para pré-qualificação dos candidatos:
- **Perguntas padrão da empresa** (já cadastradas no setup)
- **Perguntas específicas para esta vaga** (adicione aqui)

Recomendo de 3 a 5 perguntas específicas para não cansar o candidato.`
  },
  {
    id: 'review-publish',
    title: 'Revisão e Publicação',
    subtitle: 'Ativação',
    panelTitle: 'Resumo e Publicação',
    liaMessage: `Excelente! Aqui está o resumo completo da vaga.

O resumo inclui automaticamente:
- **Apresentação da empresa** (sobre, missão, visão)
- **EVP** (Employee Value Proposition)
- **Valores e cultura** da organização
- **Desafios da posição** para atrair candidatos

Revise todos os detalhes, escolha as plataformas de publicação e confirme para ativar o recrutamento.`
  },
  {
    id: 'search-calibration',
    title: 'Busca e Calibração',
    subtitle: 'Seleção',
    panelTitle: 'Busca e Calibração',
    liaMessage: `A vaga foi publicada com sucesso! Agora vou buscar candidatos compatíveis.

Para calibrar meu entendimento do perfil ideal, vou apresentar candidatos para você avaliar. Seus feedbacks me ajudam a ser mais assertiva nas próximas buscas.

Após a calibração, o kanban da vaga será populado automaticamente com os candidatos mais aderentes.`
  }
]

export const SKILLS_CATALOG: Record<string, { technical: string[]; behavioral: string[] }> = {
  'engineering': {
    technical: ['Python', 'Java', 'Node.js', 'React', 'TypeScript', 'SQL', 'Docker', 'AWS', 'Git', 'Linux', 'MongoDB', 'PostgreSQL', 'Kubernetes', 'CI/CD', 'REST API'],
    behavioral: ['Resolução de Problemas', 'Trabalho em Equipe', 'Comunicação', 'Adaptabilidade', 'Pensamento Analítico']
  },
  'finance': {
    technical: ['Excel Avançado', 'Power BI', 'SAP', 'IFRS', 'Contabilidade Geral', 'Conciliação', 'Fechamento Contábil', 'Orçamento', 'Forecast', 'Análise de Variância', 'ERP', 'SPED', 'Compliance Fiscal'],
    behavioral: ['Ética e Integridade', 'Orientação a Resultados', 'Pensamento Analítico', 'Atenção a Detalhes', 'Organização']
  },
  'hr': {
    technical: ['R&S', 'Entrevistas por Competências', 'ATS', 'LinkedIn Recruiter', 'T&D', 'Gestão de Desempenho', 'People Analytics', 'Employer Branding', 'eSocial', 'Folha de Pagamento'],
    behavioral: ['Comunicação', 'Empatia', 'Colaboração', 'Resolução de Conflitos', 'Influência']
  },
  'marketing': {
    technical: ['SEO', 'SEM', 'Google Ads', 'Meta Ads', 'Analytics', 'Copywriting', 'Social Media', 'Inbound Marketing', 'CRM', 'Growth Hacking'],
    behavioral: ['Criatividade', 'Comunicação', 'Adaptabilidade', 'Orientação a Resultados', 'Pensamento Estratégico']
  },
  'sales': {
    technical: ['Vendas Consultivas', 'CRM', 'Salesforce', 'HubSpot', 'Negociação', 'Prospecção', 'Pipeline Management', 'Forecast', 'Account Management', 'Solution Selling'],
    behavioral: ['Comunicação', 'Orientação a Resultados', 'Resiliência', 'Persuasão', 'Foco no Cliente']
  }
}

export const ROLE_AREA_MAPPING: Record<string, string> = {
  'desenvolvedor': 'engineering', 'developer': 'engineering', 'engenheiro': 'engineering', 'engineer': 'engineering',
  'programador': 'engineering', 'tech lead': 'engineering', 'arquiteto': 'engineering', 'devops': 'engineering',
  'data': 'engineering', 'cientista': 'engineering', 'fullstack': 'engineering', 'frontend': 'engineering', 'backend': 'engineering',
  'analista contábil': 'finance', 'analista fiscal': 'finance', 'analista financeiro': 'finance', 'controller': 'finance',
  'contador': 'finance', 'tesoureiro': 'finance', 'fp&a': 'finance', 'tributário': 'finance', 'controladoria': 'finance',
  'analista de rh': 'hr', 'recrutador': 'hr', 'headhunter': 'hr', 'business partner': 'hr', 'talent': 'hr',
  'dp': 'hr', 'departamento pessoal': 'hr', 'recursos humanos': 'hr', 't&d': 'hr',
  'marketing': 'marketing', 'growth': 'marketing', 'copywriter': 'marketing', 'social media': 'marketing',
  'content': 'marketing', 'seo': 'marketing', 'branding': 'marketing', 'comunicação': 'marketing',
  'vendedor': 'sales', 'vendas': 'sales', 'comercial': 'sales', 'account': 'sales', 'sales': 'sales',
  'executivo de vendas': 'sales', 'key account': 'sales', 'pré-vendas': 'sales', 'sdr': 'sales'
}

export const CORE_SKILLS_BY_ROLE: Record<string, string[]> = {
  'python': ['Python', 'Django', 'Flask', 'FastAPI', 'Pandas', 'NumPy'],
  'java': ['Java', 'Spring', 'Spring Boot', 'Hibernate', 'Maven', 'Gradle'],
  'javascript': ['JavaScript', 'TypeScript', 'Node.js', 'React', 'Vue', 'Angular'],
  'frontend': ['React', 'Vue', 'Angular', 'TypeScript', 'JavaScript', 'CSS', 'HTML'],
  'backend': ['Node.js', 'Python', 'Java', 'Go', 'SQL', 'REST API', 'GraphQL'],
  'fullstack': ['React', 'Node.js', 'TypeScript', 'SQL', 'REST API', 'Docker'],
  'data': ['Python', 'SQL', 'Pandas', 'Machine Learning', 'Power BI', 'Tableau'],
  'devops': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Terraform', 'Linux', 'Jenkins'],
  'mobile': ['React Native', 'Flutter', 'Swift', 'Kotlin', 'iOS', 'Android'],
  'analista': ['Excel', 'Power BI', 'SQL', 'SAP'],
  'financeiro': ['Excel', 'SAP', 'Power BI', 'IFRS', 'Contabilidade'],
  'rh': ['R&S', 'eSocial', 'People Analytics', 'ATS', 'LinkedIn Recruiter'],
  'marketing': ['Google Ads', 'Meta Ads', 'SEO', 'Analytics', 'CRM'],
  'comercial': ['CRM', 'Salesforce', 'HubSpot', 'Vendas Consultivas', 'Negociação'],
}

export const LEADERSHIP_KEYWORDS = ['gerente', 'coordenador', 'diretor', 'head', 'líder', 'lead', 'manager', 'supervisor', 'superintendente', 'vp', 'cto', 'ceo', 'cfo', 'coo']

export const COMMERCIAL_KEYWORDS = ['vendedor', 'vendas', 'comercial', 'account', 'sales', 'executivo de vendas', 'key account', 'sdr', 'bdr', 'closer']

export const TECHNICAL_KEYWORDS = ['desenvolvedor', 'developer', 'engenheiro', 'engineer', 'programador', 'analista de sistemas', 'arquiteto', 'devops', 'sre', 'cientista', 'data']

export const SENIORITY_LEVELS: Record<string, number> = {
  'junior': 1, 'júnior': 1, 'jr': 1, 'trainee': 1, 'estagiário': 1,
  'pleno': 2, 'pl': 2,
  'sênior': 3, 'senior': 3, 'sr': 3,
  'especialista': 4, 'principal': 4, 'staff': 4,
  'diretor': 5, 'gerente': 4, 'coordenador': 3, 'head': 5, 'líder': 3, 'lead': 3
}

export const INITIAL_JOB_CREATION_MESSAGE = `Olá! Vou te ajudar a criar uma nova vaga.

**Detalhe o máximo que puder** sobre a vaga para otimizar o processo de construção. Vou aproveitar ao máximo as informações que já tenho da sua empresa para preencher o restante!

**Exemplo de como você pode descrever:**
"Preciso de um Desenvolvedor Python Sênior para a equipe do João Silva. Vai liderar projetos de Data Science, desenvolver APIs com FastAPI e mentorar desenvolvedores júnior."

Quanto mais detalhes você fornecer, mais campos já preenchemos automaticamente:
- Cargo + Senioridade
- Gestor responsável
- Principais responsabilidades
- Competências técnicas (mínimo 3)
- Competências comportamentais (mínimo 3)
- Faixa salarial
- Vaga Afirmativa (Sim/Não)

Os campos operacionais (modelo de trabalho, localização, tipo de contrato) serão preenchidos com base nas configurações da empresa e apresentados na etapa final para sua revisão.

Digite sua descrição ou anexe um JD existente para começarmos!`

export const INITIAL_BENEFITS: JobBenefit[] = [
  { id: '1', name: 'Vale Refeição', description: '', category: 'food', value_type: 'monetary', value_details: 'R$ 35/dia', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
  { id: '2', name: 'Vale Transporte', description: '', category: 'transport', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
  { id: '3', name: 'Plano de Saúde', description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
  { id: '4', name: 'Plano Odontológico', description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
  { id: '5', name: 'Seguro de Vida', description: '', category: 'security', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
  { id: '6', name: 'Stock Options', description: '', category: 'financial', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: '7', name: 'Auxílio Home Office', description: '', category: 'quality_life', value_type: 'monetary', value_details: 'R$ 200/mês', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
  { id: '8', name: 'Auxílio Educação', description: '', category: 'education', value_type: 'monetary', value_details: 'Até R$ 500/mês', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
  { id: '9', name: 'Gympass', description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: '10', name: 'Day Off Aniversário', description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: true },
]

export const INITIAL_BEHAVIORAL_COMPETENCIES: { id: string; name: string; weight: number; justification: string; enabled: boolean }[] = [
  { id: '1', name: 'Comunicação Eficaz', weight: 4, justification: 'Colaboração com time multidisciplinar', enabled: true },
  { id: '2', name: 'Resolução de Problemas', weight: 5, justification: 'Arquitetura de sistemas complexos', enabled: true },
  { id: '3', name: 'Adaptabilidade', weight: 4, justification: 'Ambiente ágil com mudanças frequentes', enabled: true },
  { id: '4', name: 'Trabalho em Equipe', weight: 4, justification: 'Projetos colaborativos', enabled: true },
  { id: '5', name: 'Proatividade', weight: 3, justification: 'Iniciativa em melhorias técnicas', enabled: false },
]

export const INITIAL_PUBLISHING_PLATFORMS: { id: string; name: string; type: 'ats' | 'jobboard' | 'website'; enabled: boolean }[] = [
  { id: 'gupy', name: 'Gupy', type: 'ats', enabled: true },
  { id: 'pandape', name: 'Pandapé', type: 'ats', enabled: false },
  { id: 'linkedin', name: 'LinkedIn', type: 'jobboard', enabled: true },
  { id: 'indeed', name: 'Indeed', type: 'jobboard', enabled: false },
  { id: 'website', name: 'Website da Empresa', type: 'website', enabled: true },
]

export const AUTO_ADVANCE_CONFIDENCE_THRESHOLDS: Record<WizardStage, number> = {
  'input-evaluation': 0.90,
  'job-description': 0.85,
  'competencies': 0.80,
  'salary': 0.85,
  'wsi-questions': 0.75,
  'review-publish': 1.0,
  'search-calibration': 1.0
}
