# Fluxo Completo: Wizard de Criação de Vaga (ExpandedChat)

**Data:** 25 de Janeiro de 2026  
**Versão:** 3.0  
**Arquivo de Referência:** `plataforma-lia/src/components/expanded-chat-modal.tsx`  
**Objetivo:** Documentação detalhada do fluxo de criação de vagas conforme implementado no código.

> **IMPORTANTE:** Esta versão reflete a nova estrutura de 7 etapas com análise proativa de compensação e serviços integrados de inteligência.

---

## Visão Geral do Fluxo

O wizard de criação de vagas é organizado em **3 Fases** com **7 Etapas**:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        WIZARD DE CRIAÇÃO DE VAGA v3.0                          │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  FASE 1: CONSTRUÇÃO          FASE 2: ATIVAÇÃO        FASE 3: SELEÇÃO          │
│  ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────────────┐ │
│  │ 1. input-evaluation │    │                  │    │                       │ │
│  │ 2. job-description  │───▶│ 6. review-publish│───▶│ 7. search-calibration │ │
│  │ 3. competencies     │    │                  │    │                       │ │
│  │ 4. salary           │    │                  │    │                       │ │
│  │ 5. wsi-questions    │    │                  │    │                       │ │
│  └─────────────────────┘    └──────────────────┘    └───────────────────────┘ │
│                                                                                 │
│  Serviços Integrados:                                                          │
│  ├── IntelligenceLayerService        ├── CompensationAnalysisService          │
│  ├── MarketBenchmarkService          ├── SkillsCatalogService                 │
│  ├── CompanyConfigurationService     ├── RecruiterPersonalizationService      │
│  └── ConfidencePolicyService                                                   │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Tipos e Interfaces do Wizard

```typescript
// Estágios do Wizard (7 etapas)
type WizardStage = 'input-evaluation' | 'job-description' | 'competencies' | 
                   'salary' | 'wsi-questions' | 'review-publish' | 'search-calibration'

// Fases visuais
type WizardPhase = 'construction' | 'activation' | 'selection'

// Configuração das fases
const WIZARD_PHASES: WizardPhaseConfig[] = [
  { 
    id: 'construction', 
    label: 'Construção', 
    stages: ['input-evaluation', 'job-description', 'competencies', 'salary', 'wsi-questions'] 
  },
  { 
    id: 'activation', 
    label: 'Ativação', 
    stages: ['review-publish'] 
  },
  { 
    id: 'selection', 
    label: 'Seleção', 
    stages: ['search-calibration'] 
  }
]
```

---

## Serviços Integrados

O wizard utiliza uma camada de serviços para análise inteligente e sugestões:

| Serviço | Responsabilidade |
|---------|------------------|
| **IntelligenceLayerService** | Detecção de padrões, correlação de outcomes, sugestões contextuais |
| **MarketBenchmarkService** | Dados de mercado para salários, skills em alta, tendências |
| **CompanyConfigurationService** | Defaults da empresa, benefícios, estrutura organizacional |
| **CompensationAnalysisService** | Análise proativa de remuneração com benchmarks internos + mercado |
| **SkillsCatalogService** | Catálogo de skills técnicas e comportamentais por área |
| **RecruiterPersonalizationService** | Personalização baseada em histórico do recrutador |
| **ConfidencePolicyService** | Cálculo de confiança para campos inferidos |

---

## FASE 1: CONSTRUÇÃO (5 Etapas)

### Etapa 1: Input & Evaluation (`input-evaluation`)

**Descrição:** Entrada de descrição da vaga com análise proativa integrada.

**Funcionalidades:**
- Usuário descreve a vaga em linguagem natural ou anexa JD existente
- **Detecção automática de campos** via IntelligenceLayerService
- **Análise proativa de compensação** via CompensationAnalysisService
- Exibição do **CompensationAnalysisPanel** com benchmarks

**Configuração:**
```typescript
{
  id: 'input-evaluation',
  title: 'Entrada & Avaliação',
  subtitle: 'Construção',
  panelTitle: 'Análise Proativa',
  panelComponents: ['CriteriaDetectedPanel', 'CompensationAnalysisPanel'],
  liaMessage: INITIAL_JOB_CREATION_MESSAGE
}
```

**Componentes Exibidos:**
1. **CriteriaDetectedPanel** - Mostra campos detectados da descrição
2. **CompensationAnalysisPanel** - Análise de compensação com:
   - Benchmark interno (vagas similares da empresa)
   - Benchmark de mercado (dados externos)
   - Posicionamento recomendado (percentil)
   - Alertas de competitividade

**CompensationAnalysisPanel - Interface:**
```typescript
interface CompensationAnalysis {
  internalBenchmark: {
    minSalary: number
    maxSalary: number
    avgSalary: number
    sampleSize: number
    similarRoles: string[]
  }
  marketBenchmark: {
    p25: number
    p50: number
    p75: number
    p90: number
    source: string
    updatedAt: string
  }
  recommendation: {
    minSuggested: number
    maxSuggested: number
    percentile: number
    competitiveness: 'below_market' | 'at_market' | 'above_market'
    alerts: string[]
  }
}
```

**Fluxo de Dados:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT-EVALUATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Descrição do Usuário                                           │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────┐                                        │
│  │ IntelligenceLayer   │──▶ Detecta: cargo, senioridade, área   │
│  │ Service             │──▶ Extrai: skills, responsabilidades   │
│  └─────────────────────┘                                        │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────┐     ┌──────────────────────┐           │
│  │ CompensationAnalysis│◄───▶│ MarketBenchmark      │           │
│  │ Service             │     │ Service              │           │
│  └─────────────────────┘     └──────────────────────┘           │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────┐                                        │
│  │ CompensationAnalysis│ ◄─── Dados internos + mercado          │
│  │ Panel               │ ──▶ Recomendações de salário           │
│  └─────────────────────┘                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Etapa 2: Job Description (`job-description`)

**Descrição:** Revisão e edição dos campos detectados automaticamente.

**Funcionalidades:**
- Campos básicos pré-preenchidos com base na análise
- Edição inline de todos os campos
- Indicadores de origem (detectado, default, benchmark)
- Badge de confiança por campo

**Configuração:**
```typescript
{
  id: 'job-description',
  title: 'Descrição da Vaga',
  subtitle: 'Construção',
  panelTitle: 'Informações Básicas',
  liaMessage: `Preenchi com base na sua descrição e no setup da empresa.

Revise e ajuste os campos ao lado. Se precisar alterar algo, é só me dizer ou editar diretamente no painel!`
}
```

**Campos Coletados:**
| Campo | Tipologia | Origem |
|-------|-----------|--------|
| `job_title` | CRITICAL | Detectado/Manual |
| `seniority` | CRITICAL | Inferido/Manual |
| `department` | PROBABLE | Detectado/Default empresa |
| `location` | PROBABLE | Detectado/Default empresa |
| `work_model` | PROBABLE | Default empresa |
| `employment_type` | PROBABLE | Default empresa |
| `manager` | PROBABLE | Detectado/Sugerido |

**Interface:**
```typescript
interface JobDescriptionData {
  job_title: string
  seniority: 'junior' | 'pleno' | 'senior' | 'specialist' | 'lead' | 'manager' | 'director'
  department: string
  location: string
  work_model: 'presencial' | 'hibrido' | 'remoto'
  employment_type: 'clt' | 'pj' | 'estagio' | 'temporario'
  manager?: string
  responsibilities?: string[]
  field_origins: Record<string, FieldOrigin>
}
```

---

### Etapa 3: Competências (`competencies`)

**Descrição:** Definição de competências técnicas e comportamentais.

**Funcionalidades:**
- Skills do catálogo organizadas por categoria
- Inferência automática de pesos baseada em cargo/senioridade
- Níveis de proficiência (Básico, Intermediário, Avançado)
- Marcação obrigatório/desejável

**Configuração:**
```typescript
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
}
```

**Interface de Competência Técnica:**
```typescript
interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool' | 'methodology'
  weight: number // 1-5
  weightJustification?: string
  isWeightInferred?: boolean
  source: 'catalog' | 'detected' | 'manual'
}
```

**Interface de Competência Comportamental:**
```typescript
interface BehavioralCompetency {
  id: string
  name: string
  weight: number // 1-5
  justification: string
  enabled: boolean
  weightJustification?: string
  isWeightInferred?: boolean
  source: 'catalog' | 'detected' | 'manual'
}
```

**Catálogo de Skills (via SkillsCatalogService):**

| Área | Skills Técnicas | Skills Comportamentais |
|------|-----------------|------------------------|
| Engineering | Python, Java, Node.js, React, TypeScript, SQL, Docker, AWS, Kubernetes | Resolução de Problemas, Pensamento Analítico, Colaboração |
| Finance | Excel Avançado, Power BI, SAP, IFRS, Modelagem Financeira | Atenção a Detalhes, Gestão de Risco, Comunicação |
| HR | R&S, ATS, LinkedIn Recruiter, Entrevistas por Competências | Empatia, Escuta Ativa, Negociação |
| Marketing | SEO, SEM, Google Ads, Analytics, Copywriting | Criatividade, Orientação a Dados, Adaptabilidade |
| Sales | Vendas Consultivas, CRM, Salesforce, HubSpot, Negociação B2B | Persuasão, Resiliência, Foco em Resultados |

---

### Etapa 4: Remuneração (`salary`)

**Descrição:** Definição de salário e benefícios com valores sugeridos pela análise proativa.

**Funcionalidades:**
- Faixa salarial pré-preenchida com base na análise de compensação
- Comparativo visual com mercado (percentil)
- Bônus e critérios de elegibilidade
- Benefícios da empresa (auto-preenchidos) + adicionais

**Configuração:**
```typescript
{
  id: 'salary',
  title: 'Remuneração',
  subtitle: 'Construção',
  panelTitle: 'Salário e Benefícios',
  panelComponents: ['SalaryRangePanel', 'BenefitsPanel', 'MarketComparisonChart'],
  liaMessage: `Ótimo progresso! Agora vamos para remuneração e benefícios.

Os valores foram sugeridos com base na **análise de compensação** realizada:
- Benchmark interno: vagas similares da empresa
- Benchmark de mercado: dados externos atualizados

Revise e ajuste conforme necessário.`
}
```

**Interface de Salário:**
```typescript
interface SalaryInfo {
  minSalary: number
  maxSalary: number
  suggestedMin: number  // Da análise proativa
  suggestedMax: number  // Da análise proativa
  minBonus: number
  maxBonus: number
  bonusCriteria: string
  benefits: Benefit[]
  marketPosition: 'below' | 'at' | 'above'
  percentile: number
}
```

**Interface de Benefício:**
```typescript
interface Benefit {
  id: string
  name: string
  value?: string
  enabled: boolean
  source: 'company_default' | 'manual'
}
```

---

### Etapa 5: Triagem WSI (`wsi-questions`)

**Descrição:** Configuração de perguntas de triagem rápida via WhatsApp.

**Funcionalidades:**
- Perguntas padrão da empresa (configuradas no setup)
- Perguntas específicas para a vaga
- Tipos variados: aberta, sim/não, numérica, múltipla escolha
- Ordenação por batches para envio gradual

**Configuração:**
```typescript
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
}
```

**Interface de Pergunta WSI:**
```typescript
interface WSIQuestion {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean
  options?: string[]
  expectedAnswer?: string | number | boolean
  correctOptionIndex?: number
  batch: number // 1, 2, 3 para envio gradual
  category?: 'technical' | 'behavioral' | 'autodeclaracao_contexto' | 
             'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
  competency?: string // Competência avaliada
  source: 'company_default' | 'job_specific' | 'auto_generated'
}
```

---

## FASE 2: ATIVAÇÃO (1 Etapa)

### Etapa 6: Revisão e Publicação (`review-publish`)

**Descrição:** Revisão final completa e publicação nas plataformas selecionadas.

**Funcionalidades:**
- Resumo completo de todos os dados da vaga
- Edição inline de qualquer seção
- Geração automática de JD (via jd_generator_service)
- Seleção de plataformas de publicação
- Confirmação e ativação do recrutamento

**Configuração:**
```typescript
{
  id: 'review-publish',
  title: 'Revisão e Publicação',
  subtitle: 'Ativação',
  panelTitle: 'Resumo da Vaga',
  panelComponents: ['JobSummaryPanel', 'PlatformSelectionPanel'],
  liaMessage: `Excelente! Aqui está o resumo completo da vaga.

O resumo inclui automaticamente:
- **Apresentação da empresa** (sobre, missão, visão)
- **EVP** (Employee Value Proposition)
- **Valores e cultura** da organização
- **Desafios da posição** para atrair candidatos

Revise todos os detalhes. Clique em qualquer seção para editar.

Quando estiver tudo certo, selecione as **plataformas de publicação** e confirme!`
}
```

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
  { id: 'linkedin', name: 'LinkedIn Jobs', icon: 'linkedin', enabled: true, connected: true, estimatedReach: 5000 },
  { id: 'site', name: 'Site Carreiras', icon: 'globe', enabled: true, connected: true, estimatedReach: 1000 },
  { id: 'gupy', name: 'Gupy', icon: 'gupy', enabled: false, connected: false, estimatedReach: 3000 },
  { id: 'indeed', name: 'Indeed', icon: 'indeed', enabled: false, connected: false, estimatedReach: 8000 },
  { id: 'catho', name: 'Catho', icon: 'catho', enabled: false, connected: false, estimatedReach: 4000 }
]
```

---

## FASE 3: SELEÇÃO (1 Etapa)

### Etapa 7: Busca e Calibração (`search-calibration`)

**Descrição:** Busca de candidatos e calibração do perfil ideal.

**Funcionalidades:**
- Vaga publicada nas plataformas selecionadas
- Busca automática de candidatos (Pearch AI + base local)
- Apresentação de candidatos para calibração (1-5 candidatos configurável)
- Feedback do recrutador refina buscas futuras
- População automática do kanban

**Configuração:**
```typescript
{
  id: 'search-calibration',
  title: 'Busca e Calibração',
  subtitle: 'Seleção',
  panelTitle: 'Candidatos para Calibração',
  panelComponents: ['CandidateSearchPanel', 'CalibrationPanel', 'KanbanPreviewPanel'],
  liaMessage: `A vaga foi publicada com sucesso! 

Agora vou buscar candidatos compatíveis. Para calibrar meu entendimento do perfil ideal, 
vou apresentar alguns candidatos para você avaliar.

Seus feedbacks me ajudam a ser mais assertiva nas próximas buscas.

Você pode ajustar o número de candidatos para calibração (1-5) no slider acima.`
}
```

**Interface de Candidato para Calibração:**
```typescript
interface CalibrationCandidate {
  id: string
  name: string
  photoUrl?: string
  linkedinUrl?: string
  currentRole: string
  currentCompany: string
  location: string
  education: string
  overallScore: number
  highlights: { icon: string; label: string; value: string }[]
  experiences: CalibrationCandidateExperience[]
  educationHistory: CalibrationCandidateEducation[]
  skillMap: { category: string; skills: string[] }[]
  languages: string[]
  matchCriteria: CalibrationMatchCriteria[]
  averageTenure: string
  currentTenure: string
  totalExperience: string
}

interface CalibrationMatchCriteria {
  label: string
  matched: boolean
  value?: string
  weight: number
}
```

**Fluxo de Calibração:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    CALIBRATION FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Busca Inicial                                               │
│     │                                                            │
│     ├── liaApi.searchCandidatesLocal (base interna)             │
│     └── liaApi.searchCandidates (Pearch AI)                     │
│         │                                                        │
│         ▼                                                        │
│  2. Seleção para Calibração (1-5 candidatos)                    │
│     │                                                            │
│     ▼                                                            │
│  3. Recrutador avalia cada candidato                            │
│     │                                                            │
│     ├── ✅ Aprovar → Adiciona ao kanban + feedback positivo     │
│     └── ❌ Rejeitar → Feedback negativo + motivo                │
│         │                                                        │
│         ▼                                                        │
│  4. RecruiterPersonalizationService registra preferências       │
│     │                                                            │
│     ▼                                                            │
│  5. Busca refinada com perfil calibrado                         │
│     │                                                            │
│     ▼                                                            │
│  6. População automática do kanban                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hooks e Integrações

### Hooks Utilizados pelo Wizard

```typescript
import { useJobWizard } from "@/hooks/use-lia-suggestions"
import { useCompanyEligibilityQuestions } from "@/hooks/use-company-eligibility-questions"
import { useRecruitmentStages } from "@/hooks/use-recruitment-stages"
import { useJobWizardBackend } from "@/hooks/use-job-wizard-backend"
import { useWizardAutoSave } from "@/hooks/use-wizard-auto-save"
import { useCompensationAnalysis } from "@/hooks/use-compensation-analysis"
```

### Hook: useJobWizardBackend

**Arquivo:** `plataforma-lia/src/hooks/use-job-wizard-backend.ts`

**Interface de Resposta:**
```typescript
interface WizardStepResponse {
  conversation_id: string
  current_stage: number
  next_stage?: number
  stage_name: string
  lia_message: string
  detected_criteria?: DetectedCriteria
  field_origins?: Record<string, FieldOrigin>
  compensation_analysis?: CompensationAnalysis
  is_complete: boolean
  created_job?: any
  intent_detected?: string
  benchmarks?: any
  suggestions?: any
}
```

### Hook: useCompensationAnalysis

**Arquivo:** `plataforma-lia/src/hooks/use-compensation-analysis.ts`

```typescript
interface UseCompensationAnalysisReturn {
  analysis: CompensationAnalysis | null
  isLoading: boolean
  error: string | null
  fetchAnalysis: (params: {
    jobTitle: string
    seniority: string
    department: string
    location: string
  }) => Promise<void>
}
```

---

## Fluxo de Dados Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE DADOS v3.0                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Usuário                                                                 │
│     │                                                                    │
│     ▼                                                                    │
│  ┌─────────────────┐                                                    │
│  │ expanded-chat-  │ ◄──── useJobWizard                                 │
│  │ modal.tsx       │ ◄──── useCompanyEligibilityQuestions               │
│  └────────┬────────┘ ◄──── useRecruitmentStages                         │
│           │          ◄──── useJobWizardBackend                          │
│           │          ◄──── useWizardAutoSave                            │
│           │          ◄──── useCompensationAnalysis                      │
│           ▼                                                              │
│  ┌─────────────────┐                                                    │
│  │ useJobWizard    │                                                    │
│  │ Backend.ts      │───────▶ /api/backend-proxy/lia/job-wizard          │
│  └────────┬────────┘                                                    │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │                    BACKEND SERVICES                          │        │
│  ├──────────────────┬──────────────────┬───────────────────────┤        │
│  │ Intelligence     │ Compensation     │ Company               │        │
│  │ LayerService     │ AnalysisService  │ ConfigurationService  │        │
│  ├──────────────────┼──────────────────┼───────────────────────┤        │
│  │ MarketBenchmark  │ SkillsCatalog    │ RecruiterPersonal-    │        │
│  │ Service          │ Service          │ izationService        │        │
│  ├──────────────────┴──────────────────┴───────────────────────┤        │
│  │                 ConfidencePolicyService                      │        │
│  └──────────────────────────────────────────────────────────────┘        │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                    │
│  │ Database        │ ◄──── JobDraft (estado intermediário)              │
│  │                 │ ◄──── JobVacancy (após publicação)                 │
│  └─────────────────┘                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Status de Implementação

| Etapa | Status | Observações |
|-------|--------|-------------|
| 1. input-evaluation | ✅ Implementado | Análise proativa com CompensationAnalysisPanel |
| 2. job-description | ✅ Implementado | Com FieldOriginBadge e indicadores de confiança |
| 3. competencies | ✅ Implementado | Inferência de pesos automática via SkillsCatalogService |
| 4. salary | ✅ Implementado | Valores sugeridos pela análise + comparativo mercado |
| 5. wsi-questions | ✅ Implementado | Perguntas da empresa + específicas + auto-geradas |
| 6. review-publish | ✅ Implementado | Resumo completo + seleção de plataformas |
| 7. search-calibration | ✅ Implementado | Calibração flexível (1-5 candidatos) + kanban |

---

## Migração do Fluxo Anterior (10 etapas → 7 etapas)

### Mapeamento de Etapas

| Fluxo Anterior (10 etapas) | Novo Fluxo (7 etapas) | Mudança |
|---------------------------|----------------------|---------|
| 1. description | 1. input-evaluation | Expandido com análise proativa |
| 2. basic-info | 2. job-description | Renomeado, mantém funcionalidade |
| 3. competencies | 3. competencies | Mantido |
| 4. salary | 4. salary | Aprimorado com sugestões da análise |
| 5. wsi-questions | 5. wsi-questions | Mantido |
| 6. review | 6. review-publish | **Consolidado** com pre-publish |
| 7. pre-publish | 6. review-publish | **Consolidado** com review |
| 8. candidate-search | 7. search-calibration | **Consolidado** |
| 9. calibration | 7. search-calibration | **Consolidado** |
| 10. active-search | 7. search-calibration | **Consolidado** |

### Benefícios da Nova Estrutura

1. **Menos etapas** = Experiência mais fluida para o recrutador
2. **Análise proativa** na primeira etapa = Decisões informadas desde o início
3. **Consolidação lógica** = Revisão + Publicação juntas faz sentido UX
4. **Busca + Calibração unificadas** = Fluxo contínuo até kanban

---

## Changelog

| Versão | Data | Mudanças |
|--------|------|----------|
| 3.0 | 25/01/2026 | Nova estrutura 7 etapas, CompensationAnalysisService, consolidação de etapas |
| 2.0 | 25/01/2026 | Documentação das 10 etapas originais |
| 1.0 | 20/01/2026 | Versão inicial |
