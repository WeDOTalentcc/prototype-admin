# Mapeamento Completo: Menu Configurações → Wizard de Criação de Vagas

> **Versão:** 3.0  
> **Data:** Fevereiro 2026  
> **Status:** Atualizado  
> **Última Revisão:** 02 de Fevereiro de 2026

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Estrutura do Menu Configurações](#2-estrutura-do-menu-configurações)
3. [Estrutura do Wizard (3 Fases, 6 Etapas)](#3-estrutura-do-wizard-3-fases-6-etapas)
4. [Mapeamento Detalhado por Etapa do Wizard](#4-mapeamento-detalhado-por-etapa-do-wizard)
5. [CompanyData Interface Completa](#5-companydata-interface-completa)
6. [Interfaces de Configurações](#6-interfaces-de-configurações)
7. [Fluxo de Dados e Auto-preenchimento](#7-fluxo-de-dados-e-auto-preenchimento)
8. [Sistema de Learning Unificado](#8-sistema-de-learning-unificado)
9. [Arquitetura de Agentes de IA](#9-arquitetura-de-agentes-de-ia)
10. [Integrações ATS/HRIS](#10-integrações-atshris)
11. [Componentes Frontend e Backend](#11-componentes-frontend-e-backend)

---

## 1. Visão Geral

Este documento mapeia todos os campos e configurações do **Menu Configurações** da plataforma WeDo Talent para as **etapas do Wizard de Criação de Vagas**, garantindo que os recrutadores tenham uma experiência otimizada com defaults inteligentes e sugestões contextuais.

### 1.1 Princípio de Auto-preenchimento

O wizard utiliza configurações da empresa para:
- **Pré-preencher campos** com valores default da empresa
- **Sugerir skills** baseadas no tech stack cadastrado
- **Carregar benefícios** automaticamente com filtro por senioridade
- **Aplicar pipeline padrão** de etapas do processo seletivo
- **Usar perguntas de triagem** pré-configuradas pela empresa

---

## 2. Estrutura do Menu Configurações

### 2.1 Categorias e Tabs (settings-page.tsx)

```
🏢 EMPRESA
├── Dados Institucionais ──────── "institutional"
│   ├── Dados Básicos (CNPJ, razão social, etc.)
│   ├── Endereço
│   ├── Redes Sociais
│   ├── Segmento/Indústria
│   └── Filiais/Localidades
│
├── Cultura & EVP ────────────── "culture"
│   ├── Missão, Visão, Valores
│   ├── EVP (Employee Value Proposition)
│   ├── Big Five Organizacional
│   ├── Competências-chave
│   └── Iniciativas D&I
│
└── Estrutura ─────────────────── "structure"
    ├── Organograma
    ├── Departamentos
    ├── Cargos/Hierarquia
    └── Gestores

🗺️ JOURNEY MAPPING
└── Journey Mapping ──────────── "journey-mapping"
    ├── Wizard de Onboarding (5 steps)
    ├── Sistemas Usados (ATS, HRIS, etc.)
    ├── Etapas do Processo
    ├── Automações Desejadas
    └── Canais de Publicação

🔗 INTEGRAÇÕES
└── Integrações ───────────────── "integrations"
    ├── ATS (SAP, Workday, Greenhouse, etc.)
    ├── Workforce Planning
    ├── HRIS/Folha
    ├── Comunicação (Slack, Teams)
    └── Job Boards

📋 JORNADA DE RECRUTAMENTO
├── Etapas do Processo ────────── "recruitment-journey"
│   ├── Pipeline Padrão (stages)
│   ├── SLAs por Etapa
│   ├── Responsáveis
│   └── Regras de Governança
│
├── Status de Candidatos ──────── "candidate-statuses"
│   ├── Status por Stage
│   ├── Motivos de Rejeição
│   └── Motivos de Declínio
│
├── Templates de Vaga ─────────── "communication"
│   ├── Modelos de JD
│   └── Templates por Tipo de Vaga
│
└── Solicitação de Dados ──────── "data-requests"
    ├── Campos Obrigatórios
    └── Formulários Customizados

⚙️ CONFIGURAÇÕES
├── Preferências ──────────────── "preferences"
│   ├── Tema (Claro/Escuro/Sistema)
│   ├── Idioma
│   └── Fuso Horário
│
├── Notificações ──────────────── "notifications"
│   ├── Canais (Email, Push, WhatsApp, Slack)
│   └── Tipos de Notificação
│
├── Segurança ─────────────────── "security"
│   └── Privacidade e Acessos
│
├── LIA ───────────────────────── "lia"
│   ├── Personalidade/Estilo
│   ├── Sugestões Automáticas
│   ├── Insights Proativos
│   └── Modo Aprendizado
│
├── Assessment ────────────────── "assessment"
│   ├── Critérios de Avaliação
│   └── Sistema de Scoring
│
└── NPS ───────────────────────── "nps"
    └── Sistema de Feedback

🔧 ADMINISTRAÇÃO
└── ADMIN WeDOTalent ─────────── "admin-wedotalent"
    ├── Gestão de Clientes
    ├── Tenants
    └── Onboarding
```

### 2.2 Componentes Principais de Configurações

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| `CompanyTeamHub` | `CompanyTeamHub.tsx` | Dados da empresa, cultura, tech stack, benefícios, departamentos, usuários |
| `RecruitmentHub` | `RecruitmentHub.tsx` | Pipeline, perguntas screening, status, governança, configuração LIA |
| `CommunicationHub` | `CommunicationHub.tsx` | Templates de vaga e modelos de comunicação |
| `GoalsPlanningHub` | `GoalsPlanningHub.tsx` | Planejamento de contratações |
| `BenefitsTab` | `BenefitsTab.tsx` | Gestão completa de benefícios |
| `CandidateStatusesTab` | `CandidateStatusesTab.tsx` | Status e motivos de rejeição |
| `DataRequestTab` | `DataRequestTab.tsx` | Coleta de dados dos candidatos |
| `LiaFieldToggle` | `LiaFieldToggle.tsx` | Campos habilitados para LIA |

---

## 3. Estrutura do Wizard (3 Fases, 6 Etapas)

### 3.1 Diagrama do Fluxo

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        WIZARD DE CRIAÇÃO DE VAGA v4.0                          │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  FASE 1: CONSTRUÇÃO          FASE 2: ATIVAÇÃO        FASE 3: SELEÇÃO          │
│  ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────────────┐ │
│  │ 1. input-evaluation │    │                  │    │                       │ │
│  │ 2. salary           │───▶│ 5. review-publish│───▶│ 6. search-calibration │ │
│  │ 3. competencies     │    │                  │    │    (opcional: skip)   │ │
│  │ 4. wsi-questions    │    │                  │    │                       │ │
│  └─────────────────────┘    └──────────────────┘    └───────────────────────┘ │
│                                                                                 │
│  NOTA: Etapa 6 (search-calibration) pode ser pulada via opção "Pular Calibração"│
│        Economia de 5-10min para vagas sem necessidade de sourcing imediato      │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Tipos e Interfaces

```typescript
type WizardStage = 
  | 'input-evaluation' 
  | 'salary' 
  | 'competencies' 
  | 'wsi-questions' 
  | 'review-publish' 
  | 'search-calibration'

type WizardPhase = 'construction' | 'activation' | 'selection'

const WIZARD_PHASES: WizardPhaseConfig[] = [
  { 
    id: 'construction', 
    label: 'Construção', 
    stages: ['input-evaluation', 'salary', 'competencies', 'wsi-questions'] 
  },
  { 
    id: 'activation', 
    label: 'Ativação', 
    stages: ['review-publish'] 
  },
  { 
    id: 'selection', 
    label: 'Seleção', 
    stages: ['search-calibration']  // Pode ser pulada
  }
]
```

### 3.3 Opção de Pular Calibração

O wizard oferece a opção de **pular a etapa de calibração** após a publicação da vaga:

```typescript
interface SkipCalibrationConfig {
  enabled: boolean
  scenarios: [
    'vagas_urgentes',      // Tempo crítico
    'reuso_perfil',        // Perfil já calibrado
    'pool_existente',      // Candidatos já identificados
    'vaga_confidencial'    // Sem divulgação externa
  ]
  timeEstimate: {
    withCalibration: '45-60min',
    skipCalibration: '35-45min',
    timeSaved: '10-15min'
  }
}
```

---

## 4. Mapeamento Detalhado por Etapa do Wizard

### 4.1 Etapa 1: Input & Evaluation (`input-evaluation`)

**Descrição:** Entrada inicial com análise proativa de critérios, detecção automática de campos e inferência de dados básicos da vaga.

| Campo Pré-preenchido | Fonte no Menu Configurações | Componente |
|---------------------|----------------------------|------------|
| Modelo de trabalho | `CompanyData.work_model` | CompanyTeamHub → Cultura |
| Localização padrão | `CompanyData.locations[0]` | CompanyTeamHub → Filiais |
| Departamentos disponíveis | `departments[]` | CompanyTeamHub → Estrutura |
| Tech stack da empresa | `CompanyData.tech_stack` | CompanyTeamHub → Tecnologia |

**Campos Detectados Automaticamente:**

| Campo | Tipologia | Fonte no Menu Configurações | Método de Detecção |
|-------|-----------|----------------------------|-------------------|
| `job_title` | CRITICAL | Detectado/Manual | NLU + Pattern matching |
| `seniority` | CRITICAL | Inferido/Manual | Keywords + Salary hints |
| `department` | PROBABLE | `departments[]` | Context inference |
| `location` | PROBABLE | `CompanyData.locations` | Entity extraction |
| `work_model` | PROBABLE | `CompanyData.work_model` | Keywords (remoto, híbrido) |
| `employment_type` | PROBABLE | Default: CLT | Contract keywords |
| `manager` | PROBABLE | `departments[].manager` | Org chart lookup |
| `responsibilities` | INFERRED | Detectado do JD | LLM extraction |
| `affirmative_action` | OPTIONAL | Detectado do JD | D&I keywords |

**Interface:**
```typescript
interface DetectedCriteria {
  job_title: string
  seniority: 'junior' | 'pleno' | 'senior' | 'specialist' | 'lead' | 'manager' | 'director'
  department: string
  location: string
  work_model: 'presencial' | 'hibrido' | 'remoto'
  employment_type: 'clt' | 'pj' | 'estagio' | 'temporario'
  manager?: string
  responsibilities?: string[]
  affirmative_action?: {
    detected: boolean
    type: string
    confirmed: boolean
  }
  field_origins: Record<string, FieldOrigin>
}
```

**Serviços Utilizados:**
- `IntelligenceLayerService` - Detecção de padrões e campos
- `CompensationAnalysisService` - Análise proativa de compensação
- `MarketBenchmarkService` - Dados de mercado
- `AffirmativeActionDetector` - Detecção de vagas afirmativas

---

### 4.2 Etapa 2: Remuneração (`salary`)

**Descrição:** Salário, bônus e benefícios.

| Campo | Fonte no Menu Configurações | Componente |
|-------|----------------------------|------------|
| Benefícios ativos | `benefits[]` (filtro por senioridade) | CompanyTeamHub → BenefitsTab |
| Faixa salarial sugerida | Benchmark + Política interna | MarketBenchmarkService |
| Bônus padrão | Política da empresa | CompanyTeamHub → Remuneração |

**Estrutura de Benefício (BenefitsTab):**

```typescript
interface Benefit {
  id: string
  name: string
  description: string
  category: 'health' | 'food' | 'transport' | 'education' | 'financial' | 'quality_life' | 'family' | 'security'
  valueType: 'monetary' | 'percentage' | 'informative'
  value?: number
  seniorityLevel: string[]  // all, junior, pleno, senior, coordinator, manager, director, c-level
  waitingPeriod: number     // Dias de carência
  isHighlighted: boolean
  isActive: boolean
}
```

**Categorias de Benefícios:**

| Categoria | Descrição | Exemplos |
|-----------|-----------|----------|
| health | Saúde | Plano de saúde, Plano odontológico |
| food | Alimentação | VR, VA, Refeição no local |
| transport | Transporte | VT, Auxílio combustível, Estacionamento |
| education | Educação | Auxílio educação, Cursos, Certificações |
| financial | Financeiro | PLR, PPR, Previdência privada |
| quality_life | Qualidade de Vida | Gympass, Day off aniversário, Home office |
| family | Família | Auxílio creche, Licença parental estendida |
| security | Segurança | Seguro de vida, Seguro acidentes |

---

### 4.3 Etapa 3: Competências (`competencies`)

**Descrição:** Skills técnicas e comportamentais.

| Campo | Fonte no Menu Configurações | Componente |
|-------|----------------------------|------------|
| Skills técnicas sugeridas | `CompanyData.tech_stack` | CompanyTeamHub → Tecnologia |
| Idiomas padrão | `CompanyData.default_languages` | CompanyTeamHub → Cultura |
| Competências-chave | `CompanyData.coreCompetencies` | CompanyTeamHub → Cultura |
| Big Five weights | `CompanyData.*_score` | CompanyTeamHub → Big Five Radar |

**Tech Stack Categorizado (CompanyTeamHub):**

| Categoria | Ícone | Sugestões Padrão |
|-----------|-------|------------------|
| Backend | Server | Node.js, Python, Java, .NET, Go, Ruby, PHP, Rust |
| Frontend | Layout | React, Vue.js, Angular, Next.js, Svelte, TypeScript |
| Dados | Database | PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch, Snowflake |
| Cloud | Cloud | AWS, Azure, GCP, Vercel, Heroku, DigitalOcean |
| DevOps | Settings | Docker, Kubernetes, Jenkins, GitHub Actions, Terraform |
| IA/ML | Brain | TensorFlow, PyTorch, OpenAI, Anthropic, LangChain |
| ERPs | Briefcase | SAP, Oracle, Totvs, Salesforce, Dynamics 365 |
| Design | Palette | Figma, Adobe XD, Sketch, InVision, Framer |
| Mobile | Smartphone | React Native, Flutter, Swift, Kotlin, iOS, Android |

**Interface:**
```typescript
interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool' | 'methodology'
  weight: number // 1-5
  source: 'catalog' | 'detected' | 'manual'
}

interface BehavioralCompetency {
  id: string
  name: string
  weight: number // 1-5
  justification: string
  enabled: boolean
  source: 'catalog' | 'detected' | 'manual'
}
```

---

### 4.4 Etapa 4: Perguntas WSI (`wsi-questions`)

**Descrição:** Perguntas de triagem pré-configuradas.

| Campo | Fonte no Menu Configurações | Componente |
|-------|----------------------------|------------|
| Perguntas padrão | `screening_questions[]` | RecruitmentHub → Perguntas Screening |
| Banco de perguntas | `ELIGIBILITY_QUESTIONS_BANK` | eligibility-questions-bank.ts |
| Perguntas eliminatórias | Config por pergunta | RecruitmentHub |

**Perguntas de Screening Padrão (RecruitmentHub):**

```typescript
interface ScreeningQuestion {
  id: string
  question: string
  type: 'text' | 'yesno' | 'scale' | 'multiple'
  required: boolean
  order: number
  isDefault: boolean
  options?: string[]
  is_eliminatory?: boolean
  expected_answer?: string
}

// Perguntas padrão
const defaultQuestions: ScreeningQuestion[] = [
  { id: '1', question: 'Você tem interesse real nesta vaga?', type: 'yesno', required: true, order: 1, isDefault: true },
  { id: '2', question: 'Qual sua disponibilidade para início?', type: 'text', required: true, order: 2, isDefault: true },
  { id: '3', question: 'Qual sua pretensão salarial?', type: 'text', required: true, order: 3, isDefault: true },
  { id: '4', question: 'Quantos anos de experiência você tem na área?', type: 'text', required: true, order: 4, isDefault: true },
  { id: '5', question: 'Você aceita trabalhar no modelo híbrido/presencial?', type: 'yesno', required: true, order: 5, isDefault: true },
  { id: '6', question: 'Você está em algum outro processo seletivo?', type: 'yesno', required: false, order: 6, isDefault: true }
]
```

**Banco de Perguntas por Categoria:**

| Categoria | Descrição | Exemplos |
|-----------|-----------|----------|
| Elegibilidade Legal | Requisitos legais | CNH, Passaporte, Grupo elegível |
| Disponibilidade | Mobilidade e horário | Viagens, Turnos, Início imediato |
| Formação | Educação e certificações | Diploma, Certificações, Área de formação |
| Experiência | Histórico profissional | Anos de experiência, Ferramentas |
| Fit Cultural | Alinhamento cultural | Modelo de trabalho, Valores |

---

### 4.5 Etapa 5: Revisão e Publicação (`review-publish`)

**Descrição:** Consolidação e publicação da vaga.

| Campo | Fonte no Menu Configurações | Componente |
|-------|----------------------------|------------|
| Apresentação da empresa | `CompanyData.mission`, `vision`, `values` | CompanyTeamHub → Cultura |
| EVP | `CompanyData.evp_bullets` | CompanyTeamHub → Cultura |
| Descrição cultura | `CompanyData.culture_description` | CultureAnalyzer |
| D&I | `CompanyData.dei_initiatives` | CompanyTeamHub → Cultura |
| Canais de publicação | `canaisPublicacao[]` | Journey Mapping |

**Plataformas de Publicação:**

```typescript
interface PublishingPlatform {
  id: string
  name: string
  icon: string
  enabled: boolean
  connected: boolean
  estimatedReach: number
}

const AVAILABLE_PLATFORMS: PublishingPlatform[] = [
  { id: 'linkedin', name: 'LinkedIn Jobs', enabled: true, connected: true, estimatedReach: 5000 },
  { id: 'site', name: 'Site Carreiras', enabled: true, connected: true, estimatedReach: 1000 },
  { id: 'gupy', name: 'Gupy', enabled: false, connected: false, estimatedReach: 3000 },
  { id: 'indeed', name: 'Indeed', enabled: false, connected: false, estimatedReach: 8000 }
]
```

---

### 4.6 Etapa 6: Busca e Calibração (`search-calibration`)

**Descrição:** Sourcing e calibração de perfis.

| Campo | Fonte no Menu Configurações | Componente |
|-------|----------------------------|------------|
| Skills promovidas | `company_skills` (Learning) | LearningHub |
| Cutoffs calibrados | `calibration_history` | RecruiterPersonalizationService |
| Preferências do recrutador | `RecruiterProfile` | RecruiterPersonalizationService |

**Fluxo de Calibração:**

```
1. Busca Inicial (base local + Pearch AI)
     │
     ▼
2. Seleção para Calibração (1-5 candidatos)
     │
     ▼
3. Recrutador avalia cada candidato
     ├── ✅ Aprovar → Adiciona ao kanban + feedback positivo
     └── ❌ Rejeitar → Feedback negativo + motivo
     │
     ▼
4. RecruiterPersonalizationService registra preferências
     │
     ▼
5. Busca refinada com perfil calibrado
```

---

## 5. CompanyData Interface Completa

```typescript
interface CompanyData {
  // === DADOS BÁSICOS (InstitutionalTab) ===
  name: string                    // Razão Social
  tradeName: string               // Nome Fantasia
  cnpj: string                    // CNPJ
  website: string                 // Site Institucional
  email: string                   // Email Principal
  phone: string                   // Telefone Principal
  address: string                 // Endereço Completo
  logo?: string                   // URL do Logo
  industry: string                // Setor/Indústria
  size: string                    // Porte (1-10, 11-50, etc.)
  employee_count?: number         // Número de funcionários
  locations?: string[]            // Filiais/Escritórios
  linkedin_url?: string           // LinkedIn da empresa
  founded_year?: number           // Ano de fundação

  // === CULTURA E IDENTIDADE (CultureTab) ===
  mission?: string                // Missão
  vision?: string                 // Visão
  values?: string[]               // Lista de Valores
  coreCompetencies?: string[]     // Competências-chave
  work_model?: string             // Modelo: Híbrido/Remoto/Presencial
  evp_bullets?: string[]          // Employee Value Proposition
  dei_initiatives?: string        // Diversidade e Inclusão
  culture_description?: string    // Descrição da cultura

  // === TECNOLOGIA (CompanyTeamHub) ===
  tech_stack?: TechStackItem[]    // Stack de tecnologia categorizado
  engineering_culture?: string    // Cultura de engenharia
  default_languages?: string[]    // Idiomas padrão da empresa

  // === BIG FIVE DA EMPRESA (BigFiveRadar) ===
  openness_score?: number         // Abertura (0-100)
  conscientiousness_score?: number // Conscienciosidade (0-100)
  extraversion_score?: number     // Extroversão (0-100)
  agreeableness_score?: number    // Amabilidade (0-100)
  stability_score?: number        // Estabilidade Emocional (0-100)

  // === DADOS ESTRATÉGICOS (StrategicInfo) ===
  additional_data?: {
    hiring_volume?: number        // Volume mensal de contratações
    job_types?: string[]          // Tipos de vagas (CLT, PJ, etc.)
    current_ats?: string          // ATS atual
    main_challenges?: string[]    // Principais desafios de recrutamento
    main_priority?: string        // Prioridade principal
  }
}

interface TechStackItem {
  category: 'backend' | 'frontend' | 'dados' | 'cloud' | 'devops' | 'ia_ml' | 'erps' | 'design' | 'mobile'
  technologies: string[]
}
```

---

## 6. Interfaces de Configurações

### 6.1 Departamento (StructureTab)

```typescript
interface Department {
  id: string
  name: string
  description: string
  manager?: string
  manager_title?: string
  manager_email?: string
  manager_phone?: string
  headcount: number
  color: string
  members?: DepartmentMember[]
}

interface DepartmentMember {
  id: string
  name: string
  title?: string
  email?: string
  linkedin_url?: string
  level: string
  is_active: boolean
}
```

### 6.2 Pipeline de Recrutamento (RecruitmentJourneyConfig)

```typescript
interface RecruitmentStage {
  id: string
  name: string
  type: 'screening' | 'test' | 'assessment' | 'interview' | 'reference' | 'approval' | 'offer' | 'case'
  order: number
  sla_hours: number
  responsible: string
  description?: string
  is_active: boolean
  is_default: boolean
  automations?: StageAutomation[]
}

// Pipeline Padrão
const DEFAULT_STAGES: RecruitmentStage[] = [
  { order: 1, name: 'Triagem Automática', type: 'screening', sla_hours: 24, responsible: 'LIA' },
  { order: 2, name: 'Triagem Manual', type: 'screening', sla_hours: 48, responsible: 'Recrutador' },
  { order: 3, name: 'Teste Técnico', type: 'test', sla_hours: 72, responsible: 'Equipe Técnica' },
  { order: 4, name: 'Assessment/Dinâmica', type: 'assessment', sla_hours: 24, responsible: 'RH/Psicólogo' },
  { order: 5, name: 'Entrevista RH', type: 'interview', sla_hours: 48, responsible: 'Recrutador' },
  { order: 6, name: 'Entrevista Técnica', type: 'interview', sla_hours: 72, responsible: 'Tech Lead' },
  { order: 7, name: 'Entrevista com Gestor', type: 'interview', sla_hours: 48, responsible: 'Gestor' },
  { order: 8, name: 'Case/Desafio', type: 'case', sla_hours: 120, responsible: 'Equipe' },
  { order: 9, name: 'Verificação de Referências', type: 'reference', sla_hours: 48, responsible: 'RH' },
  { order: 10, name: 'Aprovação Final', type: 'approval', sla_hours: 72, responsible: 'Comitê' },
  { order: 11, name: 'Proposta/Oferta', type: 'offer', sla_hours: 24, responsible: 'RH' }
]
```

### 6.3 Regras de Governança (RecruitmentHub)

```typescript
interface GovernanceRules {
  autoScheduleInterviews: boolean        // Agendamento automático de entrevistas
  autoSendNegativeFeedback: boolean      // Envio automático de feedback negativo
  requiresValidationBeforeShortlist: boolean  // Validação antes de shortlist
}
```

### 6.4 Configuração LIA (LiaFieldToggle)

```typescript
interface LiaFieldConfig {
  field: LiaFieldKey
  enabled: boolean
  instruction?: string
}

// Campos configuráveis para LIA
type LiaFieldKey = 
  | 'mission_vision_values'
  | 'evp'
  | 'culture_description'
  | 'dei_initiatives'
  | 'tech_stack'
  | 'work_model'
  | 'departments'
  | 'benefits'
  | 'salary_policy'
  | 'hiring_goals'
  | 'recruitment_stages'
  | 'screening_questions'
  // ... outros campos
```

---

## 7. Fluxo de Dados e Auto-preenchimento

### 7.1 Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE AUTO-PREENCHIMENTO DO WIZARD                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────────────────────────────────┐  │
│  │ MENU             │     │              WIZARD                          │  │
│  │ CONFIGURAÇÕES    │────▶│                                              │  │
│  │                  │     │  Etapa 1: Input & Evaluation                 │  │
│  │ CompanyData      │     │  ├── work_model → default                    │  │
│  │ ├── tech_stack   │     │  ├── locations → dropdown                    │  │
│  │ ├── work_model   │     │  └── tech_stack → suggestions                │  │
│  │ ├── locations    │     │                                              │  │
│  │ ├── values       │     │  Etapa 2: Job Description                    │  │
│  │ └── evp_bullets  │     │  ├── departments → dropdown                  │  │
│  │                  │     │  ├── managers → dropdown                     │  │
│  │ RecruitmentHub   │     │  └── work_model → default                    │  │
│  │ ├── stages       │     │                                              │  │
│  │ ├── questions    │     │  Etapa 3: Competências                       │  │
│  │ └── governance   │     │  ├── tech_stack → skill suggestions          │  │
│  │                  │     │  ├── languages → language dropdown           │  │
│  │ BenefitsTab      │     │  └── coreCompetencies → behavioral suggest   │  │
│  │ └── benefits[]   │     │                                              │  │
│  │                  │     │  Etapa 4: Remuneração                        │  │
│  └──────────────────┘     │  └── benefits → auto-load (filter seniority) │  │
│                           │                                              │  │
│                           │  Etapa 5: Triagem WSI                        │  │
│                           │  └── screening_questions → pre-load          │  │
│                           │                                              │  │
│                           │  Etapa 6: Revisão                            │  │
│                           │  ├── mission/vision/values → apresentação    │  │
│                           │  ├── evp_bullets → EVP section               │  │
│                           │  └── dei_initiatives → D&I section           │  │
│                           │                                              │  │
│                           │  Etapa 7: Calibração                         │  │
│                           │  └── company_skills → skill filters          │  │
│                           └──────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 API de Configurações

```typescript
// Hook principal para carregar configurações
async function fetchCompanyConfig(): Promise<CompanyConfig> {
  const [companyData, recruitmentData, benefitsData] = await Promise.all([
    fetch('/api/backend-proxy/company/profile'),
    fetch('/api/backend-proxy/recruitment-journey/templates'),
    fetch('/api/backend-proxy/company/benefits')
  ])
  
  return {
    company: await companyData.json(),
    recruitment: await recruitmentData.json(),
    benefits: await benefitsData.json()
  }
}
```

---

## 8. Sistema de Learning Unificado

### 8.1 Fluxo de Aprendizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED LEARNING SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WIZARD                      LEARNING HUB                    AGENTS         │
│  ┌─────────────────┐        ┌─────────────────┐          ┌─────────────┐    │
│  │ Recrutador      │        │ LearningHub     │          │ Sourcing    │    │
│  │ confirma/rejeita│───────▶│ Service         │◀─────────│ Agent       │    │
│  │ skills/resps    │        │                 │          │             │    │
│  │                 │        │ • record_skill  │          │ WSI         │    │
│  │ POST /learning/ │        │ • record_resp   │          │ Evaluator   │    │
│  │ confirm-skill   │        │ • get_context   │          └─────────────┘    │
│  └─────────────────┘        └────────┬────────┘                             │
│                                      │                                       │
│                                      ▼                                       │
│                   ┌─────────────────────────────────────┐                    │
│                   │           DATABASE                  │                    │
│                   │ • CompanySkill (promoted após 3x)   │                    │
│                   │ • CompanyResponsibility (hash dedup)│                    │
│                   │ • AgentFeedback (histórico)         │                    │
│                   │ • CompanyPattern (padrões)          │                    │
│                   └─────────────────────────────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Catálogos Dinâmicos

| Catálogo | Tabela | Promoção | Benefício |
|----------|--------|----------|-----------|
| Skills Dinâmicas | `company_skills` | Após 3 confirmações | Sugestões personalizadas |
| Responsabilidades | `company_responsibilities` | Hash SHA256 dedup | Evita repetição |
| Padrões | `company_patterns` | Detecção automática | "77% das vagas são híbridas" |

---

## 9. Arquitetura de Agentes de IA

### 9.1 Visão Geral da Arquitetura

A plataforma LIA utiliza uma arquitetura multi-agente com 10 agentes ativos (1 orquestrador + 9 especializados) baseada no WeDOTalent Multi-Agent Architecture v2.2.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA MULTI-AGENTE LIA v2.2                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                    ORCHESTRATOR (Ag.0)                                   │   │
│  │         Roteamento, Memória, Delegação, Coordenação                      │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│    ┌───────────────────────────────────┼───────────────────────────────────┐    │
│    ▼                   ▼               ▼               ▼                   ▼    │
│  ┌────────┐  ┌────────────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Ag.1   │  │    Ag.2        │  │   Ag.3   │  │    Ag.4     │  │   Ag.5     │ │
│  │ Job    │  │   Sourcing     │  │ Triagem  │  │Entrevistador│  │ Avaliador  │ │
│  │Planner │  │   Agent        │  │Curricular│  │  WSI Voice  │  │    WSI     │ │
│  └────────┘  └────────────────┘  └──────────┘  └─────────────┘  └────────────┘ │
│                                                                                  │
│  ┌────────┐  ┌────────────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Ag.6   │  │    Ag.7        │  │   Ag.8   │  │    Ag.9     │  │ Especial   │ │
│  │Schedu- │  │   Analista     │  │Integrador│  │   Task      │  │ Recruiter  │ │
│  │ ling   │  │   Feedback     │  │   ATS    │  │  Planner    │  │ Assistant  │ │
│  └────────┘  └────────────────┘  └──────────┘  └─────────────┘  └────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Agentes Especializados

| Agente | Classe | Responsabilidades | Interação com Wizard/Settings |
|--------|--------|-------------------|------------------------------|
| **Ag.0** | Orchestrator | Roteamento, memória, delegação | Coordena todos os fluxos |
| **Ag.1** | JobIntakeAgent | Criação de vagas, extração de JD, perguntas WSI | Wizard: todas as etapas |
| **Ag.2** | SourcingAgent | Busca de candidatos (local + Pearch AI), outreach | Wizard: search-calibration |
| **Ag.3** | TriagemCurricularAgent | Parsing de CV, triagem inicial, score | Settings: Screening Rules |
| **Ag.4** | EntrevistadorAgent | Entrevistas WhatsApp/Voice, transcrição | Settings: Interview Config |
| **Ag.5** | AvaliadorWSIAgent | Avaliação científica WSI (Bloom + Dreyfus) | Settings: Assessment Config |
| **Ag.6** | SchedulingAgent | Agendamento de entrevistas (Microsoft Graph) | Settings: Calendar Config |
| **Ag.7** | AnalistaFeedbackAgent | KPIs, relatórios, feedback, comunicação | Settings: Templates |
| **Ag.8** | IntegradorATSAgent | Sincronização ATS (Gupy, Pandapé, StackOne) | Settings: Integrations |
| **Ag.9** | TaskPlannerAgent | Decomposição de tarefas, DAG, priorização | Orquestração interna |
| **Esp.** | RecruiterAssistantAgent | Briefing diário, assistência pessoal | Settings: LIA Config |

### 9.3 Interfaces de Agentes

```typescript
enum AgentType {
  ORCHESTRATOR = "orchestrator",
  JOB_PLANNER = "job_planner",
  SOURCING = "sourcing",
  CV_SCREENING = "cv_screening",
  INTERVIEWER = "interviewer",
  WSI_EVALUATOR = "wsi_evaluator",
  SCHEDULING = "scheduling",
  ANALYST_FEEDBACK = "analyst_feedback",
  ATS_INTEGRATOR = "ats_integrator",
  TASK_PLANNER = "task_planner",
  RECRUITER_ASSISTANT = "recruiter_assistant"
}

interface AgentConfig {
  type: AgentType
  enabled: boolean
  priority: 'critical' | 'high' | 'medium' | 'low'
  llmProvider: 'anthropic' | 'openai' | 'gemini'
  maxConcurrentTasks: number
  retryPolicy: {
    maxRetries: number
    backoffMs: number
  }
}
```

### 9.4 Agentes Legados (Deprecated)

Os seguintes agentes foram descontinuados e devem ser substituídos:

| Agente Legado | Substituição | Razão |
|---------------|--------------|-------|
| ScreeningAgent | TriagemCurricularAgent + EntrevistadorAgent + AvaliadorWSIAgent | Separação de responsabilidades |
| CommunicationAgent | AnalistaFeedbackAgent | Merge com analytics |
| AnalyticsAgent | AnalistaFeedbackAgent | Merge com communication |

---

## 10. Integrações ATS/HRIS

### 10.1 Provedores de ATS Suportados

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    INTEGRAÇÕES ATS/HRIS v2.0                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│   │      GUPY       │    │    PANDAPÉ      │    │   STACKONE      │            │
│   │  (API Nativa)   │    │  (API Nativa)   │    │  (Universal)    │            │
│   │                 │    │                 │    │                 │            │
│   │ • Sync vagas    │    │ • Sync vagas    │    │ • 50+ ATS       │            │
│   │ • Sync candid.  │    │ • Sync candid.  │    │ • API unificada │            │
│   │ • Webhooks      │    │ • Status sync   │    │ • Normalização  │            │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                  │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│   │     MERGE       │    │    WORKDAY      │    │      SAP        │            │
│   │  (Universal)    │    │  (Enterprise)   │    │  (Enterprise)   │            │
│   │                 │    │                 │    │                 │            │
│   │ • 200+ ATS      │    │ • HCM sync      │    │ • SuccessFactors│            │
│   │ • HRIS unified  │    │ • Requisitions  │    │ • Workforce     │            │
│   │ • Webhooks      │    │ • Approvals     │    │ • Approvals     │            │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Clientes ATS Implementados

| Provedor | Arquivo | Funcionalidades |
|----------|---------|-----------------|
| **Gupy** | `ats_clients/gupy.py` | Sync bidirecional de vagas e candidatos |
| **Pandapé** | `ats_clients/pandape.py` | Sync de vagas, candidatos, status |
| **StackOne** | `ats_clients/stackone.py` | API universal para 50+ ATS |
| **Merge** | `ats_clients/merge.py` | API unificada para 200+ ATS/HRIS |

### 10.3 Interface de Integração

```typescript
interface ATSIntegration {
  id: string
  provider: 'gupy' | 'pandape' | 'stackone' | 'merge' | 'workday' | 'sap'
  name: string
  status: 'connected' | 'disconnected' | 'pending' | 'error'
  lastSync: Date
  syncConfig: {
    syncJobs: boolean
    syncCandidates: boolean
    syncStatuses: boolean
    syncNotes: boolean
    bidirectional: boolean
    webhooksEnabled: boolean
    syncInterval: number // minutos
  }
  credentials: {
    apiKey?: string
    clientId?: string
    clientSecret?: string
    webhookSecret?: string
  }
}

// Configuração no Menu Configurações → Integrações
interface IntegrationsConfig {
  ats: ATSIntegration[]
  hris: HRISIntegration[]
  communication: CommunicationIntegration[]
  calendar: CalendarIntegration[]
  jobBoards: JobBoardIntegration[]
}
```

### 10.4 Fluxo de Sincronização

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   ATS        │     │   LIA Agent     │     │   PLATAFORMA     │
│   Externo    │────▶│   (Ag.8)        │────▶│   LIA            │
│              │     │   IntegradorATS │     │                  │
│   Gupy       │     │                 │     │   Wizard         │
│   Pandapé    │◀────│   • Normaliza   │◀────│   Kanban         │
│   StackOne   │     │   • Valida      │     │   Pipeline       │
│              │     │   • Sync        │     │                  │
└──────────────┘     └─────────────────┘     └──────────────────┘
```

### 10.5 Configuração no Menu Settings

O Menu Configurações → Integrações permite configurar:

| Seção | Campos | Descrição |
|-------|--------|-----------|
| **ATS Principal** | provider, apiKey, syncInterval | ATS principal da empresa |
| **Sync Options** | jobs, candidates, statuses | O que sincronizar |
| **Webhooks** | url, secret, events | Notificações em tempo real |
| **Mapping** | statusMap, fieldMap | Mapeamento de campos |
| **Histórico** | logs, errors, stats | Auditoria de sincronização |

---

## 11. Componentes Frontend e Backend

### 11.1 Frontend (plataforma-lia/src/)

| Arquivo | Descrição |
|---------|-----------|
| `components/pages/settings-page.tsx` | Página principal de configurações |
| `components/settings/CompanyTeamHub.tsx` | Dados da empresa, cultura, tech stack |
| `components/settings/RecruitmentHub.tsx` | Pipeline, perguntas, governança |
| `components/settings/BenefitsTab.tsx` | Gestão de benefícios |
| `components/settings/CandidateStatusesTab.tsx` | Status de candidatos |
| `components/settings/DataRequestTab.tsx` | Solicitação de dados |
| `components/settings/LiaFieldToggle.tsx` | Configuração de campos para LIA |
| `components/settings/CultureAnalyzer.tsx` | Análise de cultura |
| `components/settings/BigFiveRadar.tsx` | Radar Big Five organizacional |
| `hooks/use-job-wizard-backend.ts` | Hook de integração wizard-backend |
| `hooks/use-wizard-auto-save.ts` | Auto-save de rascunhos |
| `hooks/use-wizard-suggestions.ts` | Hook do Learning Loop (sugestões inteligentes) |
| `components/wizard/suggestion-badge.tsx` | Badge visual de fonte de dados |
| `components/job-creation/compensation-analysis-panel.tsx` | Análise de compensação |
| `components/job-creation/field-origin-badge.tsx` | Badge de origem do campo |
| `types/wizard-suggestions.ts` | Tipos TypeScript do Learning Loop |

### 11.2 Backend (lia-agent-system/app/)

#### Modelos e Schemas

| Arquivo | Descrição |
|---------|-----------|
| `models/job_draft.py` | Modelo JobDraft e histórico |
| `models/recruiter_profile.py` | Perfil e preferências do recrutador |
| `schemas/field_typology.py` | Tipologia de campos |

#### Serviços

| Arquivo | Descrição |
|---------|-----------|
| `services/confidence_policy_service.py` | Cálculo de confiança |
| `services/skills_catalog_service.py` | Catálogo de skills |
| `services/intelligence_layer_service.py` | Camada de inteligência |
| `services/recruiter_personalization_service.py` | Personalização por recrutador |
| `services/jd_template_service.py` | Geração de JD |
| `services/learning_hub_service.py` | Sistema de aprendizado unificado |
| `services/wsi_service.py` | Serviço WSI para perguntas e avaliação |
| `services/notification_service.py` | Notificações multicanal |

#### Integrações ATS/HRIS

| Arquivo | Descrição |
|---------|-----------|
| `services/ats_clients/base.py` | Interface base para clientes ATS |
| `services/ats_clients/gupy.py` | Cliente para integração Gupy |
| `services/ats_clients/pandape.py` | Cliente para integração Pandapé |
| `services/ats_clients/stackone.py` | Cliente universal StackOne (50+ ATS) |
| `services/ats_clients/merge.py` | Cliente universal Merge (200+ ATS/HRIS) |

#### Agentes Especializados

| Arquivo | Descrição |
|---------|-----------|
| `agents/base_agent.py` | Classe base para todos os agentes |
| `agents/agent_registry.py` | Registro central de agentes |
| `agents/job_wizard_graph.py` | Grafo de estados do wizard |
| `agents/specialized/job_intake_agent.py` | Ag.1: Criação de vagas |
| `agents/specialized/sourcing_agent.py` | Ag.2: Busca de candidatos |
| `agents/specialized/triagem_curricular_agent.py` | Ag.3: Triagem de CVs |
| `agents/specialized/entrevistador_agent.py` | Ag.4: Entrevistas WSI |
| `agents/specialized/avaliador_wsi_agent.py` | Ag.5: Avaliação científica |
| `agents/specialized/scheduling_agent.py` | Ag.6: Agendamento |
| `agents/specialized/analista_feedback_agent.py` | Ag.7: Analytics e feedback |
| `agents/specialized/integrador_ats_agent.py` | Ag.8: Integração ATS |
| `agents/specialized/task_planner_agent.py` | Ag.9: Planejamento de tarefas |
| `agents/specialized/recruiter_assistant_agent.py` | Assistente pessoal |

#### APIs

| Arquivo | Descrição |
|---------|-----------|
| `api/v1/job_drafts.py` | Endpoints de drafts |
| `api/v1/intelligence.py` | Endpoints de inteligência |
| `api/v1/wizard_suggestions.py` | Endpoints do Learning Loop (7 endpoints) |
| `api/v1/ats.py` | Endpoints de integração ATS |
| `api/v1/calibration.py` | Endpoints de calibração |
| `api/v1/wsi_questions.py` | Endpoints de perguntas WSI |

---

## Tabela Resumo: Mapeamento Wizard ↔ Configurações

| Etapa do Wizard | Campos Pré-preenchidos | Fonte no Menu Configurações |
|-----------------|----------------------|------------------------------|
| **1. Input & Evaluation** | Cargo, senioridade, modelo de trabalho, localização, responsabilidades | CompanyTeamHub (Cultura, Filiais, Tecnologia) + IntelligenceLayer |
| **2. Remuneração (Salary)** | Faixa salarial, bônus, benefícios ativos (por senioridade) | CompanyTeamHub → BenefitsTab + MarketBenchmark |
| **3. Competências** | Skills técnicas, idiomas, competências comportamentais, Big Five | CompanyTeamHub (Tech Stack, Idiomas, Cultura) |
| **4. Perguntas WSI** | Perguntas padrão, banco de perguntas, perguntas eliminatórias | RecruitmentHub → Screening Questions |
| **5. Revisão e Publicação** | Missão, visão, valores, EVP, D&I, canais de publicação | CompanyTeamHub (Cultura & EVP) + Journey Mapping |
| **6. Busca e Calibração** | Skills promovidas, cutoffs calibrados, preferências do recrutador | LearningHub + RecruiterPersonalization |

### Agentes Envolvidos por Etapa

| Etapa | Agente Principal | Agentes de Suporte |
|-------|------------------|-------------------|
| 1. Input & Evaluation | JobIntakeAgent (Ag.1) | IntelligenceLayerService |
| 2. Remuneração | JobIntakeAgent (Ag.1) | MarketBenchmarkService |
| 3. Competências | JobIntakeAgent (Ag.1) | SkillsCatalogService |
| 4. Perguntas WSI | JobIntakeAgent (Ag.1) | WSIService |
| 5. Revisão e Publicação | JobIntakeAgent (Ag.1) | IntegradorATSAgent (Ag.8) |
| 6. Busca e Calibração | SourcingAgent (Ag.2) | RecruiterPersonalizationService |

---

**Última atualização:** 02 de Fevereiro de 2026  
**Versão do Documento:** 3.0  
**Arquitetura de Agentes:** v2.2 (10 agentes ativos)  
**Etapas do Wizard:** 6 (3 fases)
