# Mapeamento Completo: Menu Configurações → Wizard de Criação de Vagas

> **Objetivo:** Documentar TODOS os campos disponíveis no menu Configurações para consumo pela LIA  
> **Versão:** 3.0 | **Data:** 28 Janeiro 2026  
> **Fontes Primárias:**
> - `CompanyTeamHub.tsx` - Empresa & Equipe
> - `RecruitmentHub.tsx` - Recrutamento
> - `GoalsPlanningHub.tsx` - Planejamento

---

## 📋 ESTRUTURA REAL DO MENU (conforme screenshot)

```
🏢 Empresa & Equipe (20% preenchido)
├── Dados da Empresa ──────── CompanyTeamHub → "company-data"
│   ├── Informações Básicas
│   ├── Cultura e Identidade  
│   ├── Tech Stack
│   ├── Big Five da Empresa
│   └── Idiomas Padrão
├── Informações Estratégicas ── CompanyTeamHub → "strategic-info"
├── Departamentos ──────────── CompanyTeamHub → "departments"
├── Benefícios ─────────────── CompanyTeamHub → "benefits" (BenefitsTab)
└── Usuários ───────────────── CompanyTeamHub → "users" (UserManagement)

⚙️ Recrutamento (0% preenchido)
├── Pipeline ───────────────── RecruitmentHub → "pipeline"
├── Perguntas Screening ────── RecruitmentHub → "screening"
├── Status de Candidatos ───── RecruitmentHub → "candidate-statuses"
└── Solicitação de Dados ───── RecruitmentHub → "data-requests"

📊 Planejamento
└── Planejamento de Contratações ─ GoalsPlanningHub
    ├── Workforce Planning (por departamento/mês)
    ├── Metas de Recrutadores
    └── Alertas Automatizados
```

---

## 1️⃣ EMPRESA & EQUIPE → "company-data"

### 1.1 CompanyData Interface (TODOS os campos)

```typescript
interface CompanyData {
  // === DADOS BÁSICOS ===
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
  company_size?: string           // Tamanho textual
  headquarters?: string           // Sede principal
  locations?: string[]            // Filiais/Escritórios
  founded_year?: number           // Ano de fundação
  linkedin_url?: string           // LinkedIn da empresa

  // === CULTURA E IDENTIDADE ===
  mission?: string                // Missão
  vision?: string                 // Visão
  values?: string[]               // Lista de Valores
  coreCompetencies?: string[]     // Competências-chave
  work_model?: string             // Modelo: Híbrido/Remoto/Presencial
  growth_opportunities?: string   // Oportunidades de crescimento
  team_dynamics?: string          // Dinâmica de equipe
  leadership_style?: string       // Estilo de liderança
  evp_bullets?: string[]          // Employee Value Proposition
  dei_initiatives?: string        // Diversidade e Inclusão
  sustainability?: string         // Sustentabilidade
  social_impact?: string          // Impacto Social

  // === TECNOLOGIA ===
  tech_stack?: string[]           // Stack de tecnologia categorizado
  engineering_culture?: string    // Cultura de engenharia
  default_languages?: string[]    // Idiomas padrão da empresa

  // === BIG FIVE DA EMPRESA ===
  openness_score?: number         // Abertura (0-100)
  conscientiousness_score?: number // Conscienciosidade (0-100)
  extraversion_score?: number     // Extroversão (0-100)
  agreeableness_score?: number    // Amabilidade (0-100)
  stability_score?: number        // Estabilidade Emocional (0-100)

  // === DADOS ESTRATÉGICOS (additional_data) ===
  additional_data?: {
    hiring_volume?: number        // Volume mensal de contratações
    job_types?: string[]          // Tipos de vagas (CLT, PJ, etc.)
    current_ats?: string          // ATS atual
    main_challenges?: string[]    // Principais desafios de recrutamento
    main_priority?: string        // Prioridade principal
    platform_expectations?: string // Expectativas da plataforma
    communication_channels?: string[] // Canais de comunicação
    allow_lia_contact?: boolean   // Permitir contato da LIA
    additional_notes?: string     // Notas adicionais
    responsible_name?: string     // Responsável pelo recrutamento
    responsible_position?: string // Cargo do responsável
    preferred_contact_time?: string // Horário preferido de contato
    onboarding_completed_at?: string // Data conclusão onboarding
  }
}
```

### 1.2 Tech Stack Categorizado

A empresa pode cadastrar tecnologias em 9 categorias:

| Categoria | Ícone | Sugestões Padrão |
|-----------|-------|------------------|
| **Backend** | Server | Node.js, Python, Java, .NET, Go, Ruby, PHP, Rust |
| **Frontend** | Layout | React, Vue.js, Angular, Next.js, Svelte, TypeScript |
| **Dados** | Database | PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch |
| **Cloud** | Cloud | AWS, Azure, GCP, Vercel, Heroku, DigitalOcean |
| **DevOps** | Settings | Docker, Kubernetes, Jenkins, GitHub Actions, Terraform |
| **IA/ML** | Brain | TensorFlow, PyTorch, OpenAI, Anthropic, LangChain |
| **ERPs** | Briefcase | SAP, Oracle, Totvs, Salesforce, Dynamics 365 |
| **Design** | Palette | Figma, Adobe XD, Sketch, InVision, Framer |
| **Mobile** | Smartphone | React Native, Flutter, Swift, Kotlin, iOS, Android |

**Uso no Wizard:**
- Sugerir competências técnicas baseadas nas stacks da empresa
- Validar se tecnologia mencionada é usada internamente
- Auto-completar requisitos técnicos

---

## 2️⃣ EMPRESA & EQUIPE → "strategic-info"

### 2.1 Informações Estratégicas de Recrutamento

| Campo | Descrição | Uso no Wizard |
|-------|-----------|---------------|
| `hiring_volume` | Volume mensal de contratações | Contextualizar prioridade |
| `current_ats` | ATS atual da empresa | Integração |
| `work_model` | Modelo de trabalho padrão | **Pré-preencher modelo** |
| `job_types` | Tipos de vagas (CLT, PJ, Estágio) | **Dropdown de contrato** |
| `main_challenges` | Desafios de recrutamento | Contextualizar LIA |
| `main_priority` | Prioridade principal | Ordenar sugestões |
| `platform_expectations` | Expectativas da LIA | Personalizar comportamento |
| `communication_channels` | Canais preferidos | Notificações |
| `responsible_name` | Nome do responsável RH | Atribuição padrão |
| `responsible_position` | Cargo do responsável | Hierarquia |

---

## 3️⃣ EMPRESA & EQUIPE → "departments"

### 3.1 Estrutura de Departamento

```typescript
interface Department {
  id: string
  name: string              // Nome do departamento
  description: string       // Descrição
  manager?: string          // Nome do gestor
  manager_title?: string    // Cargo do gestor
  manager_email?: string    // Email do gestor
  manager_phone?: string    // Telefone do gestor
  headcount: number         // Número de funcionários
  color: string             // Cor para identificação visual
  members?: DepartmentMember[]
}

interface DepartmentMember {
  id: string
  name: string
  title?: string            // Cargo
  email?: string
  phone?: string
  linkedin_url?: string
  avatar_url?: string
  level: string             // Nível hierárquico
  is_active: boolean
}
```

**Uso no Wizard:**
- **Dropdown de Departamento** (Etapa 2)
- **Dropdown de Gestor Responsável** filtrado por departamento
- **Requisitante da Vaga** (lista de gestores)
- Contexto para sugestões de perfil

---

## 4️⃣ EMPRESA & EQUIPE → "benefits"

### 4.1 Estrutura de Benefício

```typescript
interface Benefit {
  id: string
  name: string              // Nome do benefício
  description: string       // Descrição detalhada
  category: string          // Categoria (ver abaixo)
  valueType: 'monetary' | 'percentage' | 'informative'
  value?: number            // Valor se monetário/percentual
  seniorityLevel: string[]  // Níveis que recebem
  waitingPeriod: number     // Dias de carência
  isHighlighted: boolean    // Destaque na divulgação
  isActive: boolean         // Ativo/Inativo
}
```

### 4.2 Categorias de Benefícios

| ID | Categoria | Exemplos |
|----|-----------|----------|
| `health` | Saúde & Bem-estar | Plano de saúde, Gympass, Saúde mental |
| `food` | Alimentação | VR, VA, Refeição no local |
| `transport` | Transporte | VT, Estacionamento, Fretado |
| `education` | Educação & Desenvolvimento | Cursos, MBA, Certificações |
| `financial` | Financeiro | PLR, Previdência, Empréstimo consignado |
| `quality_life` | Qualidade de Vida | Home office, Day off, Short friday |
| `family` | Família | Auxílio-creche, Licença estendida |
| `security` | Segurança | Seguro de vida, Acidentes pessoais |

### 4.3 Níveis de Senioridade

| ID | Nome |
|----|------|
| `all` | Todos os Níveis |
| `junior` | Júnior |
| `pleno` | Pleno |
| `senior` | Sênior |
| `coordinator` | Coordenação+ |
| `manager` | Gerência+ |
| `director` | Diretoria |
| `c-level` | C-Level |

### 4.4 Períodos de Carência

| Dias | Descrição |
|------|-----------|
| 0 | Imediato |
| 30 | 30 dias |
| 60 | 60 dias |
| 90 | 90 dias |
| 180 | 6 meses |
| 365 | 1 ano |

**Uso no Wizard (Etapa 5):**
- Lista todos os benefícios ativos
- Filtra por senioridade da vaga
- Destaca benefícios marcados como `isHighlighted`
- Mostra valores quando disponíveis

---

## 5️⃣ EMPRESA & EQUIPE → "users"

### 5.1 Estrutura de Usuário/Recrutador

```typescript
interface CompanyUser {
  id: string
  name: string
  email: string
  role: string              // Papel: Admin, Recrutador, Gestor
  department: string        // Departamento
  isActive: boolean
  avatar_url?: string
  permissions: string[]     // Lista de permissões
}
```

**Uso no Wizard:**
- **Atribuir responsável pela vaga**
- **Selecionar recrutador líder**
- Notificações e aprovações

---

## 6️⃣ RECRUTAMENTO → "pipeline"

### 6.1 Etapas do Processo Seletivo

```typescript
interface RecruitmentStage {
  id: string
  name: string              // Nome da etapa
  type: string              // screening, test, interview, case, reference, offer
  duration: string          // Duração esperada
  sla: number               // SLA em horas
  description: string       // Descrição
  responsible: string       // Responsável padrão
  isOptional: boolean       // Etapa opcional?
  hasAutomation: boolean    // Tem automação?
  hasEmailTemplate: boolean // Tem template de email?
  criteria: string[]        // Critérios de avaliação
  order: number             // Ordem no funil
}
```

### 6.2 Etapas Padrão Disponíveis

| Ordem | Etapa | Tipo | SLA | Responsável | Opcional |
|-------|-------|------|-----|-------------|----------|
| 1 | Triagem Automática | screening | 24h | LIA | ❌ |
| 2 | Triagem Manual | screening | 48h | Recrutador | ❌ |
| 3 | Teste Técnico | test | 72h | Equipe Técnica | ✅ |
| 4 | Assessment/Dinâmica | assessment | 24h | RH/Psicólogo | ✅ |
| 5 | Entrevista RH | interview | 48h | Recrutador | ❌ |
| 6 | Entrevista Técnica | interview | 72h | Tech Lead | ❌ |
| 7 | Entrevista com Gestor | interview | 48h | Gestor | ❌ |
| 8 | Case/Desafio | case | 120h | Equipe | ✅ |
| 9 | Verificação de Referências | reference | 48h | RH | ✅ |
| 10 | Aprovação Final | approval | 72h | Comitê | ❌ |
| 11 | Proposta/Oferta | offer | 24h | RH | ❌ |

**Uso no Wizard (Etapa 7):**
- Carrega template de pipeline completo
- Permite ligar/desligar etapas opcionais
- Calcula timeline baseado em SLAs
- Sugere responsáveis por etapa

---

## 7️⃣ RECRUTAMENTO → "screening"

### 7.1 Perguntas de Screening Padrão

```typescript
interface ScreeningQuestion {
  id: string
  question: string          // Texto da pergunta
  type: 'text' | 'yesno' | 'scale' | 'multiple'
  required: boolean         // Obrigatória?
  order: number             // Ordem de exibição
  isDefault: boolean        // Pergunta padrão da empresa?
  options?: string[]        // Opções para multiple choice
}
```

### 7.2 Perguntas Padrão Cadastradas

| # | Pergunta | Tipo | Obrigatória |
|---|----------|------|-------------|
| 1 | Você tem interesse real nesta vaga? | yesno | ✅ |
| 2 | Qual sua disponibilidade para início? | text | ✅ |
| 3 | Qual sua pretensão salarial? | text | ✅ |
| 4 | Quantos anos de experiência você tem na área? | text | ✅ |
| 5 | Você aceita trabalhar no modelo híbrido/presencial? | yesno | ✅ |
| 6 | Você está em algum outro processo seletivo? | yesno | ❌ |

**Uso no Wizard (Etapa 6):**
- Carrega automaticamente todas as perguntas ativas
- Permite adicionar perguntas específicas da vaga
- Mantém perguntas obrigatórias sempre selecionadas

### 7.3 Perguntas Adicionais Sugeridas (IMPLEMENTAR)

> Banco de perguntas contextuais que a LIA pode sugerir baseado no tipo de vaga

#### 📋 ELEGIBILIDADE E REQUISITOS LEGAIS

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 1 | Esta vaga é afirmativa. Você se identifica com o grupo elegível? | yesno | Vagas afirmativas (PCD, negros, mulheres, LGBTQIA+, 50+) |
| 2 | Se sim, qual grupo você se identifica? | multiple | Seguimento da pergunta anterior |
| 3 | Você possui laudo/CID que comprove a deficiência? | yesno | Vagas PCD |
| 4 | Você possui CNH válida? | yesno + text | Vagas que exigem habilitação |
| 5 | Qual categoria da sua CNH? (A, B, C, D, E) | multiple | Seguimento - motoristas, vendedores externos |
| 6 | Você possui veículo próprio para uso no trabalho? | yesno | Vendas externas, representantes |
| 7 | Você possui passaporte válido? | yesno | Vagas com viagens internacionais |
| 8 | Você possui visto de trabalho para [país]? | yesno | Vagas internacionais |

#### ✈️ DISPONIBILIDADE E MOBILIDADE

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 9 | Você tem disponibilidade para viagens frequentes? | yesno | Comercial, consultoria, auditoria |
| 10 | Qual percentual do tempo você aceitaria viajar? | scale | 0-100% - Seguimento |
| 11 | Você tem disponibilidade para mudança de cidade/estado? | yesno | Vagas em outras localidades |
| 12 | Você aceitaria trabalhar em turnos/escalas? | yesno | Operações, indústria, varejo |
| 13 | Você tem disponibilidade para trabalhar aos finais de semana? | yesno | Varejo, operações, suporte |
| 14 | Você tem disponibilidade para trabalhar em horário noturno? | yesno | Operações, suporte 24h |
| 15 | Você pode iniciar imediatamente ou está cumprindo aviso prévio? | text | Urgência da contratação |

#### 🎓 FORMAÇÃO E CERTIFICAÇÕES

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 16 | Você possui formação superior completa? | yesno | Vagas que exigem diploma |
| 17 | Qual sua área de formação? | text | Seguimento |
| 18 | Você possui pós-graduação/MBA? | yesno | Cargos de liderança |
| 19 | Você possui certificação [X] válida? | yesno | Certificações específicas (PMP, AWS, CPA, etc.) |
| 20 | Você está cursando faculdade atualmente? | yesno | Vagas de estágio |
| 21 | Qual semestre você está cursando? | text | Seguimento estágio |
| 22 | Você possui registro ativo no [conselho]? | yesno | CRM, CRC, CREA, OAB, etc. |

#### 💼 EXPERIÊNCIA ESPECÍFICA

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 23 | Você já trabalhou com [ferramenta/sistema]? | yesno | ERP, SAP, Salesforce, etc. |
| 24 | Quantos anos de experiência com [tecnologia]? | text | Tech, engenharia |
| 25 | Você já liderou equipes? Se sim, de quantas pessoas? | text | Cargos de gestão |
| 26 | Você já atuou no segmento [indústria]? | yesno | Experiência setorial |
| 27 | Você tem experiência com vendas B2B ou B2C? | multiple | Comercial |
| 28 | Qual seu ticket médio/meta atingida no último ano? | text | Vendas |

#### 🌍 IDIOMAS

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 29 | Qual seu nível de inglês? | scale | Básico/Intermediário/Avançado/Fluente |
| 30 | Você tem certificação de inglês? (TOEFL, IELTS, Cambridge) | yesno + text | Vagas que exigem comprovação |
| 31 | Qual seu nível de espanhol? | scale | Empresas latam |
| 32 | Você é fluente em outros idiomas? Quais? | text | Multinacionais |

#### 💰 REMUNERAÇÃO E CONTRATO

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 33 | Você aceita contratação PJ? | yesno | Vagas PJ |
| 34 | Você aceita contrato temporário? | yesno | Projetos, sazonais |
| 35 | A faixa salarial de R$ X a R$ Y está alinhada com sua expectativa? | yesno | Alinhamento de expectativas |
| 36 | Você tem CNPJ ativo ou disponibilidade para abrir? | yesno | Vagas PJ |

#### 🏠 MODELO DE TRABALHO

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 37 | Você tem estrutura para home office? (internet, espaço, equipamento) | yesno | Vagas remotas |
| 38 | Você mora na região metropolitana de [cidade]? | yesno | Vagas híbridas/presenciais |
| 39 | Qual a distância aproximada da sua casa até o escritório em [endereço]? | text | Logística |

#### ⚠️ COMPLIANCE E CONFLITO DE INTERESSES

| # | Pergunta | Tipo | Contexto de Uso |
|---|----------|------|-----------------|
| 40 | Você possui cláusula de não-competição com empregador atual? | yesno | Cargos estratégicos |
| 41 | Você tem parentes trabalhando nesta empresa? | yesno | Política de nepotismo |
| 42 | Você já trabalhou nesta empresa anteriormente? | yesno | Recontratação |
| 43 | Você possui alguma pendência trabalhista com esta empresa? | yesno | Histórico |

### 7.4 Interface Estendida de Perguntas

```typescript
interface ScreeningQuestionExtended extends ScreeningQuestion {
  // === CAMPOS ADICIONAIS ===
  category: 'eligibility' | 'availability' | 'education' | 'experience' | 
            'languages' | 'compensation' | 'work_model' | 'compliance' | 'general'
  
  trigger_condition?: {
    field: string           // Campo da vaga que ativa a pergunta
    operator: 'equals' | 'contains' | 'greater_than'
    value: string | number  // Valor que ativa
  }
  
  follow_up_question_id?: string  // ID da pergunta de seguimento
  
  eliminatory?: boolean     // Resposta errada elimina candidato
  eliminatory_answer?: string | boolean  // Qual resposta elimina
  
  ai_suggestion?: boolean   // LIA pode sugerir baseado no contexto
  
  validation_regex?: string // Regex para validar resposta text
  placeholder?: string      // Placeholder para campo text
}
```

**Exemplos de Trigger Conditions:**

```typescript
// Pergunta aparece só se vaga for afirmativa
{
  trigger_condition: {
    field: 'is_affirmative',
    operator: 'equals',
    value: true
  }
}

// Pergunta aparece só se exigir viagens
{
  trigger_condition: {
    field: 'travel_required',
    operator: 'equals',
    value: true
  }
}

// Pergunta aparece só para vagas de liderança
{
  trigger_condition: {
    field: 'seniority_level',
    operator: 'contains',
    value: 'coordinator|manager|director'
  }
}
```

---

## 8️⃣ PLANEJAMENTO → "workforce"

### 8.1 Planejamento de Contratações

```typescript
interface MonthlyPlanning {
  jan: number, feb: number, mar: number, apr: number,
  may: number, jun: number, jul: number, aug: number,
  sep: number, oct: number, nov: number, dec: number
}

interface Position {
  id: string
  name: string                    // Nome do cargo
  monthlyPlanned: MonthlyPlanning // Quantidade por mês
}

interface DepartmentData {
  id: string
  name: string                    // Nome do departamento
  positions: Position[]           // Cargos planejados
  expanded: boolean
}
```

**Uso no Wizard:**
- Validar se vaga está no planejamento
- Alertar vagas fora do plano
- Sugerir priorização baseada em metas

---

## 📊 RESUMO: MAPEAMENTO WIZARD ↔ CONFIGURAÇÕES

| Etapa do Wizard | Campos Pré-preenchidos | Fonte |
|-----------------|----------------------|-------|
| **Etapa 1 - Detecção** | Validação de modelo de trabalho, localização, departamento | `CompanyData.work_model`, `locations` |
| **Etapa 2 - Básicas** | Departamento, Gestor, Localização, Modelo | `departments[]`, `managers[]`, `headquarters` |
| **Etapa 3 - Técnicos** | Sugestões de stack, Idiomas | `tech_stack[]`, `default_languages[]` |
| **Etapa 4 - Comportamentais** | Valores, Competências, Big Five | `values[]`, `coreCompetencies[]`, `*_score` |
| **Etapa 5 - Benefícios** | TODOS os benefícios ativos | `BenefitsTab` com filtro por senioridade |
| **Etapa 6 - Triagem** | Perguntas padrão | `screening_questions[]` |
| **Etapa 7 - Entrevistas** | Pipeline completo | `recruitment_stages[]` |
| **Etapa 8 - Revisão** | Timeline, Governança | Calculado de SLAs |

---

## 9️⃣ INTEGRAÇÕES → ATS/HRIS (JÁ EXISTE)

> Arquivo: `plataforma-lia/src/components/pages/ats-integrations-page.tsx`

### 9.1 Sistemas Suportados

| Sistema | Tipo | Features |
|---------|------|----------|
| **SAP SuccessFactors** | HRIS | Candidatos, Vagas, Entrevistas, Ofertas, Onboarding |
| **Workday HCM** | HRIS | Funcionários, Requisições, Performance, Benefícios |
| **BambooHR** | HRIS | Colaboradores, Relatórios, Time Off, Performance |
| **Greenhouse** | ATS | Candidatos, Vagas, Entrevistas, Scorecards |

### 9.2 Interface de Integração

```typescript
interface ATSSystem {
  id: string
  name: string
  type: 'sap' | 'workday' | 'bamboohr' | 'greenhouse' | 'custom'
  status: 'connected' | 'connecting' | 'error' | 'disabled'
  lastSync?: string
  totalRecords: number
  syncedRecords: number
  features: string[]
  webhookUrl?: string
  apiEndpoint?: string
}

interface Integration {
  id: string
  name: string
  system: ATSSystem
  isActive: boolean
  frequency: 'realtime' | 'hourly' | 'daily' | 'weekly'
  direction: 'import' | 'export' | 'bidirectional'
  mappedFields: number
}
```

**Uso no Wizard:**
- Sincronizar vagas do Workforce Planning automaticamente
- Importar requisições de headcount do HRIS
- Exportar vagas criadas para o ATS da empresa

---

## 🔧 CAMPOS E FUNCIONALIDADES A CRIAR

### 🔴 PRIORIDADE ALTA

#### A. Política de Recrutamento da Empresa

```typescript
interface RecruitmentPolicy {
  // === REQUISITOS OBRIGATÓRIOS GLOBAIS ===
  required_languages?: {
    language: string        // 'english', 'spanish', 'portuguese'
    min_level: string       // 'basic', 'intermediate', 'advanced', 'fluent'
    applies_to: string[]    // ['all'] ou ['tech', 'sales', 'leadership']
  }[]
  
  required_work_model?: {
    model: 'remote' | 'hybrid' | 'onsite' | 'flexible'
    is_mandatory: boolean
    exceptions_allowed: boolean
    exception_approver?: string
  }
  
  required_competencies?: {
    competency: string      // 'comunicacao', 'trabalho_em_equipe', etc.
    min_score?: number      // Score mínimo no assessment
    applies_to: string[]    // Departamentos ou 'all'
  }[]

  // === SLAs GLOBAIS ===
  global_slas: {
    job_opening_approval: number     // Dias para aprovar abertura
    shortlist_delivery: number       // Dias para entregar shortlist
    job_closure: number              // Dias máx para fechar vaga
    candidate_feedback: number       // Dias máx para dar feedback
    offer_response: number           // Dias para candidato responder
  }

  // === REGRAS DE GOVERNANÇA ===
  governance: {
    require_job_approval: boolean
    min_candidates_shortlist: number
    max_days_without_update: number
    require_rejection_reason: boolean
    require_interview_notes: boolean
  }
}
```

**Onde criar:** Nova tab em Recrutamento → "Políticas"

#### B. Sync Workforce Planning → Vagas

```typescript
interface WorkforcePlanningSync {
  enabled: boolean
  sync_frequency: 'monthly_start' | 'weekly' | 'manual'
  auto_create_draft: boolean        // Criar rascunho automático
  notify_recruiter: boolean         // Notificar recrutador
  include_job_details: boolean      // Puxar descrição do cargo
  
  // Mapeamento de campos do planejamento para a vaga
  field_mapping: {
    position_name: string           // → job.title
    department: string              // → job.department
    seniority: string               // → job.seniority_level
    headcount: number               // → job.positions_count
    target_date: string             // → job.target_start_date
  }
}
```

**Onde criar:** GoalsPlanningHub → nova seção "Sincronização"

### 🟡 PRIORIDADE MÉDIA

#### C. Faixas Salariais por Nível

```typescript
interface SalaryRanges {
  currency: string                  // 'BRL', 'USD'
  ranges: {
    seniority: string               // 'junior', 'pleno', 'senior', etc.
    department?: string             // Opcional: por departamento
    min_salary: number
    max_salary: number
    bonus_target?: number           // % de bônus
    updated_at: string
  }[]
}
```

**Onde criar:** Planejamento → "Faixas Salariais"

#### D. Tipos de Contrato Permitidos

```typescript
interface ContractTypes {
  allowed_types: {
    type: 'clt' | 'pj' | 'estagio' | 'temporario' | 'terceiro' | 'freelancer'
    is_active: boolean
    requires_approval: boolean
    approval_level?: string         // 'manager', 'director', 'hr'
    default_benefits?: string[]     // IDs dos benefícios padrão
  }[]
}
```

**Onde criar:** CompanyData → "Tipos de Contrato"

### 🟢 PRIORIDADE BAIXA

#### E. Níveis de Senioridade da Empresa

```typescript
interface SeniorityLevels {
  levels: {
    id: string
    name: string                    // 'Trainee', 'Júnior', 'Pleno', etc.
    order: number
    min_experience_years?: number
    typical_salary_range?: string   // Referência a SalaryRanges
    career_track: 'individual' | 'management' | 'specialist'
  }[]
}
```

**Onde criar:** CompanyData → "Estrutura de Cargos"

---

## 🧠 LEARNING HUB SYSTEM (Janeiro 2026)

> **Novo:** Sistema de aprendizado unificado que melhora sugestões com base no histórico da empresa.

### Arquitetura do Learning Hub

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED LEARNING SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WIZARD STAGES 1-7            LEARNING HUB                    AGENTS        │
│  ┌─────────────────┐          ┌─────────────────┐          ┌─────────────┐  │
│  │ Recrutador      │          │ LearningHub     │          │ Sourcing    │  │
│  │ confirma/rejeita│─────────▶│ Service         │◀─────────│ Agent       │  │
│  │ skills/resps    │          │                 │          │             │  │
│  │                 │          │ • record_skill  │          │ WSI         │  │
│  │ POST /learning/ │          │ • record_resp   │          │ Evaluator   │  │
│  │ confirm-skill   │          │ • get_context   │          └─────────────┘  │
│  └─────────────────┘          └────────┬────────┘                           │
│                                        │                                     │
│                                        ▼                                     │
│                     ┌─────────────────────────────────────────┐              │
│                     │           DATABASE                      │              │
│                     │ • CompanySkill (promoted após 3x)       │              │
│                     │ • CompanyResponsibility (hash dedup)    │              │
│                     │ • AgentFeedback (histórico)             │              │
│                     │ • CompanyPattern (padrões detectados)   │              │
│                     └─────────────────────────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Catálogos Dinâmicos (por Empresa)

| Catálogo | Tabela | Promoção | Benefício |
|----------|--------|----------|-----------|
| **Skills Dinâmicas** | `company_skills` | Após 3 confirmações | Sugestões personalizadas por empresa |
| **Responsabilidades** | `company_responsibilities` | Hash SHA256 dedup | Evita repetição, melhora qualidade |
| **Padrões** | `company_patterns` | Detecção automática | "77% das vagas são híbridas" |

### Novos Métodos nos Catálogos

```python
# SkillsCatalogService.suggest_skills_with_learning()
async def suggest_skills_with_learning(
    db: AsyncSession,
    company_id: str,
    role: str,
    seniority: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Retorna skills mescladas (dinâmicas + estáticas):
    - technical_skills: Lista mesclada
    - company_learned_skills: Skills promovidas da empresa
    - source_mix: {"dynamic": 3, "static": 7}
    """

# ResponsibilitiesCatalogService.suggest_responsibilities_with_learning()
async def suggest_responsibilities_with_learning(
    db: AsyncSession,
    company_id: str,
    role: str,
    seniority: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Retorna responsabilidades mescladas priorizando aprendidas
    """
```

### Endpoints de Learning

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/lia/learning/confirm-skill` | POST | Registra confirmação/rejeição de skill |
| `/lia/learning/confirm-responsibility` | POST | Registra responsabilidade (com dedup) |
| `/lia/learning/context` | POST | Retorna contexto de learning da empresa |

### Stages 8-10 com Agentes

| Stage | Endpoint | Agente | Learning |
|-------|----------|--------|----------|
| 8 | `/wizard/stage8/search` | Sourcing Agent | Usa skills promovidas em buscas |
| 8 | `/wizard/stage8/feedback` | - | Registra feedback de seleções |
| 9 | `/wizard/stage9/evaluate` | WSI Evaluator | Usa cutoffs calibrados |
| 9 | `/wizard/stage9/calibrate` | - | Ajusta cutoffs por padrões |
| 10 | `/wizard/stage10/start-sourcing` | Sourcing Agent | Sourcing proativo |
| 10 | `/wizard/stage10/outreach` | - | Outreach automatizado |
| 10 | `/wizard/stage10/feedback` | - | Registra taxas de engajamento |

### Isolamento Multi-Tenant

Todos os dados de learning são isolados por `company_id`:
- Skills de Empresa A **nunca** aparecem para Empresa B
- Padrões são calculados apenas com dados históricos da própria empresa
- Feedback de agentes é segregado por empresa

### Arquivos do Learning Hub

| Componente | Arquivo |
|------------|---------|
| LearningHubService | `lia-agent-system/app/services/learning_hub_service.py` |
| SkillsCatalogService | `lia-agent-system/app/services/skills_catalog_service.py` |
| ResponsibilitiesCatalogService | `lia-agent-system/app/services/responsibilities_catalog_service.py` |
| Models (CompanySkill, etc.) | `lia-agent-system/app/models/company_learning.py` |
| Integration Tests | `lia-agent-system/app/tests/test_learning_loop_integration.py` |

---

## 📊 RESUMO COMPLETO: WIZARD ↔ CONFIGURAÇÕES

| Etapa do Wizard | Campos Pré-preenchidos | Fonte | Status |
|-----------------|----------------------|-------|--------|
| **Etapa 1 - Detecção** | Modelo de trabalho, localização | `CompanyData`, `RecruitmentPolicy` | ⚠️ Parcial |
| **Etapa 2 - Básicas** | Departamento, Gestor, Modelo | `departments[]`, `managers[]` | ✅ OK |
| **Etapa 3 - Técnicos** | Stack, Idiomas, Skills aprendidas | `tech_stack[]`, `LearningHub.company_skills` | ✅ OK |
| **Etapa 4 - Comportamentais** | Competências obrigatórias | `coreCompetencies[]`, `RecruitmentPolicy.required_competencies` | ⚠️ Parcial |
| **Etapa 5 - Benefícios** | Benefícios ativos | `BenefitsTab` | ✅ OK |
| **Etapa 6 - Triagem** | Perguntas padrão | `screening_questions[]` | ✅ OK |
| **Etapa 7 - Entrevistas** | Pipeline com SLAs | `recruitment_stages[]` + SLAs | ✅ OK |
| **Etapa 8 - Sourcing** | Skills promovidas, Buscas | `LearningHub.get_learning_context()`, Sourcing Agent | ✅ OK |
| **Etapa 9 - WSI Evaluation** | Cutoffs calibrados | `LearningHub.get_calibration_context()`, WSI Evaluator | ✅ OK |
| **Etapa 10 - Active Sourcing** | Histórico de engajamento | `LearningHub.outreach_patterns` | ✅ OK |

---

## 📁 ARQUIVOS FONTE

| Componente | Arquivo |
|------------|---------|
| CompanyTeamHub | `plataforma-lia/src/components/settings/CompanyTeamHub.tsx` |
| RecruitmentHub | `plataforma-lia/src/components/settings/RecruitmentHub.tsx` |
| GoalsPlanningHub | `plataforma-lia/src/components/settings/GoalsPlanningHub.tsx` |
| BenefitsTab | `plataforma-lia/src/components/settings/BenefitsTab.tsx` |
| UserManagement | `plataforma-lia/src/components/settings/user-management.tsx` |
| BigFiveRadar | `plataforma-lia/src/components/settings/BigFiveRadar.tsx` |
| RecruitmentJourneyConfig | `plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx` |


---

## 🔗 ANÁLISE: WIZARD ONBOARDING ↔ DADOS DA EMPRESA

> *Integração do conteúdo de `wizard-vs-settings-analysis.md`*

### Status de Integração Atual

| Métrica | Wizard Onboarding | Dados da Empresa | Status |
|---------|-------------------|------------------|--------|
| Total de campos | 22 | 45+ | Diferente |
| Campos compartilhados | 14 | 14 | ✅ Integrados |
| Campos exclusivos do Wizard | 10 | - | ⚠️ Não migram |
| Campos exclusivos de Dados | - | 31 | ⚠️ Não preenchidos pelo Wizard |

### Campos INTEGRADOS (funcionam corretamente)

| # | Wizard Field | Settings Field | Status |
|---|--------------|----------------|--------|
| 1 | `companyName` | `name` (Razão Social) | ✅ |
| 2 | `logoUrl` | `logo` | ✅ |
| 3 | `sector` | `industry` (Setor) | ✅ |
| 4 | `employeeCount` | `size` | ✅ |
| 5 | `website` | `website` | ✅ |
| 6 | `linkedinUrl` | `linkedin_url` | ✅ |
| 7 | `responsibleEmail` | `email` | ✅ |
| 8 | `responsiblePhone` | `phone` | ✅ |
| 9 | `cultureProfile.mission` | `mission` | ✅ |
| 10 | `cultureProfile.vision` | `vision` | ✅ |
| 11 | `cultureProfile.values` | `values` | ✅ |
| 12 | `cultureProfile.evp_bullets` | `evp_bullets` | ✅ |
| 13 | `cultureProfile.core_competencies` | `coreCompetencies` | ✅ |
| 14 | Big Five scores (5 campos) | Big Five scores | ✅ |

### Campos do WIZARD que NÃO MIGRAM

| # | Campo Wizard | Descrição | Onde deveria aparecer? |
|---|--------------|-----------|------------------------|
| 1 | `hiringVolume` | Volume de contratações mensal | `additional_data.hiring_volume` |
| 2 | `jobTypes` | Tipos de vagas | `additional_data.job_types` |
| 3 | `currentAts` | ATS atual | `additional_data.current_ats` |
| 4 | `mainChallenges` | Desafios principais | `additional_data.main_challenges` |
| 5 | `mainPriority` | Prioridade principal | `additional_data.main_priority` |
| 6 | `platformExpectations` | Expectativas | `additional_data.platform_expectations` |
| 7 | `communicationChannels` | Canais preferidos | `additional_data.communication_channels` |
| 8 | `allowLiaContact` | Permite contato LIA | `additional_data.allow_lia_contact` |
| 9 | `additionalNotes` | Notas adicionais | `additional_data.additional_notes` |
| 10 | `responsibleName` | Nome do responsável | `additional_data.responsible_name` |
| 11 | `responsiblePosition` | Cargo do responsável | `additional_data.responsible_position` |
| 12 | `preferredContactTime` | Horário preferido | `additional_data.preferred_contact_time` |

### Backend API Flow

```
Wizard Submit (/api/backend-proxy/onboarding/submit)
         │
         ▼
┌─────────────────────────────────────────────┐
│  Dados Salvos no CompanyProfile:            │
│  ✅ company_name, logo_url, sector          │
│  ✅ employee_count, website, linkedin_url   │
│  ✅ responsible_email, responsible_phone    │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Dados Salvos no CultureProfile:            │
│  ✅ mission, vision, values                 │
│  ✅ evp_bullets, core_competencies          │
│  ✅ Big Five scores (5 campos)              │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Dados que deveriam ir para additional_data:│
│  ⚠️ hiring_volume, job_types, current_ats   │
│  ⚠️ main_challenges, main_priority          │
│  ⚠️ platform_expectations                   │
│  ⚠️ communication_channels, allow_lia_contact│
│  ⚠️ responsible_name, responsible_position  │
│  ⚠️ preferred_contact_time, additional_notes│
└─────────────────────────────────────────────┘
```

### Matriz de Status por Seção

| Seção Settings | % Integrado com Wizard | Campos Faltando |
|----------------|------------------------|-----------------|
| Dados da Empresa | 60% | tradeName, cnpj, address, work_model |
| Cultura/Valores | 95% | Gerados automaticamente pela LIA |
| Departamentos | 0% | Não coletado no wizard |
| Benefícios | 0% | Não coletado no wizard |
| Usuários | 0% | Não coletado no wizard |

### Recomendações

**Prioridade Alta:**
1. Estender endpoint `/onboarding/submit` para salvar campos em `additional_data`
2. Adicionar campos `tradeName`, `CNPJ` e `work_model` ao wizard

**Prioridade Média:**
3. Criar seção "Perfil de Recrutamento" na tela Dados da Empresa
4. Sincronizar campo `currentAts` com Integration Hub

**Prioridade Baixa:**
5. Campos gerados pela análise de cultura já funcionam via CultureAnalyzer

---

## 📁 ARQUIVOS FONTE

| Componente | Arquivo |
|------------|---------|
| CompanyTeamHub | `plataforma-lia/src/components/settings/CompanyTeamHub.tsx` |
| RecruitmentHub | `plataforma-lia/src/components/settings/RecruitmentHub.tsx` |
| GoalsPlanningHub | `plataforma-lia/src/components/settings/GoalsPlanningHub.tsx` |
| BenefitsTab | `plataforma-lia/src/components/settings/BenefitsTab.tsx` |
| UserManagement | `plataforma-lia/src/components/settings/user-management.tsx` |
| BigFiveRadar | `plataforma-lia/src/components/settings/BigFiveRadar.tsx` |
| RecruitmentJourneyConfig | `plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx` |

| Onboarding Wizard | `plataforma-lia/src/components/settings/onboarding-wizard.tsx` |
| Backend Onboarding | `lia-agent-system/app/api/v1/onboarding.py` |
| Backend Company | `lia-agent-system/app/api/v1/company.py` |

---

## 📝 CHANGELOG

| Data | Versão | Alteração |
|------|--------|-----------|
| 28/01/2026 | 3.0 | Adição do Learning Hub System (Stages 8-10), catálogos dinâmicos, endpoints de learning |
| 22/01/2026 | 2.3 | Adição de 43 perguntas adicionais de triagem por categoria com trigger conditions |
| 22/01/2026 | 2.2 | Adição de ATS/HRIS Integrations, RecruitmentPolicy, SLAs globais, WorkforcePlanningSync |
| 22/01/2026 | 2.1 | Unificação com wizard-vs-settings-analysis.md |
| 22/01/2026 | 2.0 | Revisão completa com todos os campos reais das interfaces TypeScript |
| 16/12/2025 | 1.0 | Versão inicial wizard-vs-settings-analysis.md |
