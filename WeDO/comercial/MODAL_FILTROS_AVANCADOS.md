# Modal de Filtros Avançados - Documentação Técnica

**Versão**: 1.0  
**Data**: Dezembro 2024  
**Plataforma**: WeDo Talent / Plataforma LIA  

---

## Índice

1. [Visão Geral](#1-visão-geral)
   - [1.1 Arquitetura do Componente](#11-arquitetura-do-componente)
   - [1.2 Stack Tecnológica](#12-stack-tecnológica)
2. [Origens de Busca](#2-origens-de-busca)
   - [2.1 Tipos de Busca](#21-tipos-de-busca)
   - [2.2 Cálculo de Créditos](#22-cálculo-de-créditos-busca-globalhíbrida)
3. [Estrutura de Dados](#3-estrutura-de-dados)
   - [3.1 Interface Principal de Filtros](#31-interface-principal-de-filtros)
4. [Catálogo de Campos (53 Campos)](#4-catálogo-de-campos-53-campos)
   - [4.1 Seção: Origem da Busca](#41-seção-origem-da-busca)
   - [4.2 Seção: Opções de Busca (PPI Options)](#42-seção-opções-de-busca-ppi-options)
   - [4.3 Seção: Geral](#43-seção-geral)
   - [4.4 Seção: Perfil Profissional](#44-seção-perfil-profissional)
   - [4.5 Seção: Localização](#45-seção-localização)
   - [4.6 Seção: Cargo e Função](#46-seção-cargo-e-função)
   - [4.7 Seção: Empresa](#47-seção-empresa)
   - [4.8 Seção: Habilidades](#48-seção-habilidades)
   - [4.9 Seção: Formação](#49-seção-formação)
   - [4.10 Seção: Idiomas](#410-seção-idiomas)
5. [Dicionário de Dados - Definições Detalhadas](#5-dicionário-de-dados---definições-detalhadas-dos-campos)
   - [5.1 Campos Gerais](#51-campos-gerais)
   - [5.2 Campos de Localização](#52-campos-de-localização)
   - [5.3 Campos de Cargo e Função](#53-campos-de-cargo-e-função)
   - [5.4 Campos de Empresa](#54-campos-de-empresa)
   - [5.5 Campos de Habilidades](#55-campos-de-habilidades)
   - [5.6 Campos de Formação Acadêmica](#56-campos-de-formação-acadêmica)
   - [5.7 Campos de Idiomas](#57-campos-de-idiomas)
   - [5.8 Campos de Opções de Busca (PPI)](#58-campos-de-opções-de-busca-ppi)
   - [5.9 Campos de Origem da Busca](#59-campos-de-origem-da-busca)
   - [5.10 Resumo: Cálculo de Tempo de Experiência](#510-resumo-cálculo-de-tempo-de-experiência)
   - [5.11 Resumo: Tempo no Cargo vs Permanência Média](#511-resumo-tempo-no-cargo-vs-permanência-média)
6. [Sistema de Busca Semântica (LLM-Powered)](#6-sistema-de-busca-semântica-llm-powered)
   - [6.1 Campos com Busca Semântica](#61-campos-com-busca-semântica)
   - [6.2 Arquitetura da Busca Semântica](#62-arquitetura-da-busca-semântica)
   - [6.3 Hook Frontend: useSemanticSearch](#63-hook-frontend-usesemanticsearch)
   - [6.4 Backend: Serviço Semântico](#64-backend-serviço-semântico)
   - [6.5 Endpoints da API](#65-endpoints-da-api)
7. [Componentes de Input Especializados](#7-componentes-de-input-especializados)
   - [7.1 SkillsFilterInput](#71-skillsfilterinput)
   - [7.2 ExpertiseAreasInput](#72-expertiseareasinput)
   - [7.3 IndustryFilterInput](#73-industryfilterinput)
   - [7.4 FieldsOfStudyInput](#74-fieldsofstudyinput)
   - [7.5 CompanyFilterInput](#75-companyfilterinput)
   - [7.6 LocationFilterInput](#76-locationfilterinput)
8. [Sistema de Presets](#8-sistema-de-presets)
   - [8.1 Presets de Cargos](#81-presets-de-cargos)
   - [8.2 Presets de Universidades](#82-presets-de-universidades)
9. [Integração com Pearch API](#9-integração-com-pearch-api)
   - [9.1 Conversão de Filtros](#91-conversão-de-filtros)
   - [9.2 Mapeamento de Campos](#92-mapeamento-de-campos)
10. [Design System](#10-design-system)
    - [10.1 Cores](#101-cores)
    - [10.2 Tipografia](#102-tipografia)
    - [10.3 Componentes de Badge](#103-componentes-de-badge)
11. [Performance](#11-performance)
    - [11.1 Otimizações Implementadas](#111-otimizações-implementadas)
    - [11.2 Métricas Alvo](#112-métricas-alvo)
12. [Destinos de Salvamento](#12-destinos-de-salvamento)
13. [Navegação Lateral](#13-navegação-lateral)
14. [Fluxo de Aplicação de Filtros](#14-fluxo-de-aplicação-de-filtros)
15. [Testes e Validação](#15-testes-e-validação)
    - [15.1 Casos de Teste Recomendados](#151-casos-de-teste-recomendados)
16. [Considerações para Migração](#16-considerações-para-migração)
    - [16.1 Vue.js + Nuxt](#161-vuejs--nuxt)
    - [16.2 Ruby on Rails](#162-ruby-on-rails)
17. [Arquivos Chave](#17-arquivos-chave)
18. [Variáveis de Ambiente](#18-variáveis-de-ambiente)
19. [Changelog](#19-changelog)

---

## 1. Visão Geral

O Modal de Filtros Avançados é um componente central da plataforma de recrutamento que permite buscas sofisticadas de candidatos com 53 campos de filtro. Suporta três origens de busca (Local, Híbrida, Global) com integração à base Pearch AI (800M+ perfis).

### 1.1 Arquitetura do Componente

```
plataforma-lia/src/components/search/
├── advanced-filters-modal.tsx     # Componente principal (~3100 linhas)
├── SkillsFilterInput.tsx          # Input com busca semântica
├── ExpertiseAreasInput.tsx        # Áreas de expertise com LLM
├── CompanyFilterInput.tsx         # Empresas com autocomplete
├── ExcludedCompaniesInput.tsx     # Exclusão de empresas
├── IndustryFilterInput.tsx        # Setores com busca semântica
├── FieldsOfStudyInput.tsx         # Áreas de estudo
├── CompanyTagsInput.tsx           # Tags de empresa
├── CompanyHQLocationsInput.tsx    # Sede da empresa
├── FundingStagesInput.tsx         # Estágio de funding
├── UniversitiesFilterInput.tsx    # Universidades
├── ExcludedUniversitiesInput.tsx  # Exclusão de universidades
├── UniversityLocationsInput.tsx   # Localização de universidades
├── DegreeRequirementsInput.tsx    # Grau acadêmico
├── GraduationYearInput.tsx        # Ano de formatura
├── LocationFilterInput.tsx        # Localização do candidato
├── PastLocationsInput.tsx         # Localizações anteriores
├── RadiusDropdown.tsx             # Raio de busca
├── LanguageFilterInput.tsx        # Idiomas
└── credit-confirmation-dialog.tsx # Confirmação de créditos
```

### 1.2 Stack Tecnológica

| Camada | Tecnologias |
|--------|-------------|
| Frontend | React 18, TypeScript, Next.js 14, Tailwind CSS |
| UI Components | Radix UI, shadcn/ui, Lucide Icons |
| Backend API | FastAPI (Python 3.11) |
| Busca Semântica | Google Gemini 1.5 Flash |
| Cache | Redis (TTL 10min) + SWR Frontend |
| Base Global | Pearch AI (800M+ perfis) |

---

## 2. Origens de Busca

### 2.1 Tipos de Busca

| Origem | Descrição | Custo Base | Latência |
|--------|-----------|------------|----------|
| **Local** | Base interna do cliente | Gratuito | < 500ms |
| **Híbrida** | Local primeiro, depois Global | 1 crédito/candidato | 1-3s |
| **Global** | Pearch AI (800M+ perfis) | 1 crédito/candidato | 2-5s |

### 2.2 Cálculo de Créditos (Busca Global/Híbrida)

```typescript
// Fórmula de custo por candidato:
const baseCost = searchType === "fast" ? 1 : 5;  // Fast vs Pro
const insights = 2;                                // Sempre incluído
const freshness = highFreshness ? 2 : 0;          // Dados atualizados
const emailCost = (requireEmails ? 1 : 0) + (showEmails ? 2 : 0);
const phoneCost = (requirePhoneNumbers ? 1 : 0) + (showPhoneNumbers ? 14 : 0);

const costPerCandidate = baseCost + insights + freshness + emailCost + phoneCost;
```

#### Tabela de Custos Detalhada

| Opção | Custo Adicional | Descrição |
|-------|-----------------|-----------|
| Busca Rápida (Fast) | +1 crédito | Dados básicos |
| Busca Profissional (Pro) | +5 créditos | Dados completos |
| Insights + Scoring | +2 créditos | Sempre incluído |
| Dados Atualizados | +2 créditos | Perfis em tempo real |
| Apenas com Email | +1 crédito | Filtra por disponibilidade |
| Mostrar Emails | +2 créditos | Exibe emails nos resultados |
| Apenas com Telefone | +1 crédito | Filtra por disponibilidade |
| Mostrar Telefones | +14 créditos | **Alto custo** - exibe telefones |
| Email OU Telefone | +1 crédito | Pelo menos um contato |

---

## 3. Estrutura de Dados

### 3.1 Interface Principal de Filtros

```typescript
export interface SearchFilters {
  ppiOptions?: {
    searchType?: "fast" | "pro"
    highFreshness?: boolean
    strictFilters?: boolean
    requireEmails?: boolean
    showEmails?: boolean
    requirePhoneNumbers?: boolean
    showPhoneNumbers?: boolean
    requirePhonesOrEmails?: boolean
    openToWorkOnly?: boolean
  }
  searchOptions?: {
    includeDiscovered?: boolean
  }
  general?: {
    minExperience?: number
    maxExperience?: number
    hideViewedProfiles?: boolean
    hideViewedScope?: HideViewedScope
    hideViewedPeriod?: HideViewedPeriod
  }
  locations?: {
    locations?: string[]
    locationItems?: LocationItem[]
    countries?: string[]
    radius?: RadiusValue
    timezone?: string | null
    pastLocations?: PastLocationItem[]
  }
  job?: {
    titles?: string[]
    titleScope?: "current_only" | "current_recent" | "current_past"
    pastTitles?: string[]
    levels?: string[]
    roles?: string[]
    timeInRoleMin?: string
    timeInRoleMax?: string
    minAverageTenure?: string
  }
  company?: {
    companyItems?: CompanyItem[]
    companyTimeFilter?: CompanyTimeFilter
    specificYears?: { start: number; end: number }
    fundingStages?: string[]
    excludedCompanyItems?: ExcludedCompanyItem[]
    excludedTimeFilter?: ExcludedTimeFilter
    excludeDNC?: boolean
    industries?: string[]
    industryTimeFilter?: IndustryTimeFilter
    companyTags?: CompanyTagItem[]
    companyTagsTimeFilter?: CompanyTagsTimeFilter
    companyHQLocations?: string[]
    companyHQTimeFilter?: CompanyHQTimeFilter
    companySizes?: string[]
    companyFoundedAfter?: number
  }
  skills?: {
    skillItems?: SkillItem[]
    expertise?: string[]
  }
  education?: {
    universities?: string[]
    excludedUniversities?: string[]
    universityLocations?: string[]
    degreeRequirementMode?: 'regular' | 'nested'
    degree?: string | null
    degrees?: string[]
    fieldsOfStudyMode?: 'regular' | 'nested'
    fieldsOfStudy?: string[]
    graduationYearMin?: number | null
    graduationYearMax?: number | null
  }
  languages?: {
    languages?: string[]
    proficiencyLevel?: string
  }
  profile?: {
    isDecisionMaker?: boolean
    isTopUniversities?: boolean
    isStartup?: boolean
  }
}
```

---

## 4. Catálogo de Campos (53 Campos)

### 4.1 Seção: Origem da Busca

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 1 | Origem da Busca | RadioGroup | N/A | `searchSource` | local \| hybrid \| global |
| 2 | Incluir Descobertos | Switch | N/A | `includeDiscovered` | Candidatos de buscas anteriores |

### 4.2 Seção: Opções de Busca (PPI Options)

| # | Campo | Tipo | Custo | API Parameter | Descrição |
|---|-------|------|-------|---------------|-----------|
| 3 | Tipo de Busca | Select | +1/+5 | `pearch_type` | fast \| pro |
| 4 | Dados Atualizados | Switch | +2 | `high_freshness` | Perfis em tempo real |
| 5 | Filtros Rigorosos | Switch | 0 | `strict_filters` | Matching exato de títulos |
| 6 | Apenas com Email | Switch | +1 | `require_emails` | Filtrar por email |
| 7 | Mostrar Emails | Switch | +2 | `show_emails` | Exibir emails |
| 8 | Apenas com Telefone | Switch | +1 | `require_phone_numbers` | Filtrar por telefone |
| 9 | Mostrar Telefones | Switch | +14 | `show_phone_numbers` | Exibir telefones |
| 10 | Email OU Telefone | Switch | +1 | `require_phones_or_emails` | Pelo menos um contato |

### 4.3 Seção: Geral

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 11 | Experiência Mínima | Number | N/A | `years_experience_min` | Anos de experiência |
| 12 | Experiência Máxima | Number | N/A | `years_experience_max` | Anos de experiência |
| 13 | Ocultar Visualizados (Escopo) | Select | N/A | `hide_viewed_scope` | 8 opções de escopo |
| 14 | Ocultar Visualizados (Período) | Select | N/A | `hide_viewed_period` | 5 opções de período |

#### Opções de Escopo (HideViewedScope)

```typescript
type HideViewedScope = 
  | "dont_hide"                    // Não ocultar
  | "by_you_this_project"          // Visualizados por você neste projeto
  | "by_you_all_projects"          // Visualizados por você em todos os projetos
  | "shortlisted_by_you"           // Shortlistados por você
  | "by_org_this_project"          // Visualizados pela org neste projeto
  | "by_org_all_projects"          // Visualizados pela org em todos
  | "shortlisted_org_this_project" // Shortlistados pela org neste projeto
  | "shortlisted_org_all_projects" // Shortlistados pela org em todos
```

### 4.4 Seção: Perfil Profissional

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 15 | Aberto a Oportunidades | Switch | N/A | `is_open_to_work` | LinkedIn Open to Work |
| 16 | Decisor / Líder | Switch | N/A | `is_decision_maker` | Posições de liderança |
| 17 | Top Universidades | Switch | N/A | `is_top_universities` | Formados em elite |
| 18 | Experiência em Startup | Switch | N/A | `is_startup` | Cultura ágil |

### 4.5 Seção: Localização

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 19 | Localização | TagInput + Autocomplete | N/A | `locations`, `countries` | Cidades e países |
| 20 | Raio de Busca | Dropdown | N/A | `radius` | 10mi, 25mi, 50mi, 100mi, 250mi |
| 21 | Timezone | Select | N/A | `timezone` | Fuso horário do candidato |
| 22 | Localizações Anteriores | TagInput | N/A | `past_locations` | Onde já morou |

#### Opções de Raio

```typescript
type RadiusValue = '10mi' | '25mi' | '50mi' | '100mi' | '250mi'
```

### 4.6 Seção: Cargo e Função

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 23 | Cargos | TagInput + Presets | **SIM** | `titles` | Busca semântica LLM |
| 24 | Escopo do Cargo | Dropdown | N/A | `title_scope` | current_only, current_recent, current_past |
| 25 | Cargos Anteriores | TagInput | **SIM** | `past_titles` | Histórico de cargos |
| 26 | Nível de Senioridade | Chips | N/A | `seniority_levels` | 8 níveis |
| 27 | Funções/Roles | TagInput | **SIM** | `job_functions` | Áreas funcionais |
| 28 | Tempo no Cargo (Min) | Select | N/A | `time_in_role_min` | 3m a 15 anos |
| 29 | Tempo no Cargo (Max) | Select | N/A | `time_in_role_max` | 3m a 15 anos |
| 30 | Tenure Médio Mínimo | Select | N/A | `min_average_tenure` | Estabilidade |

#### Níveis de Senioridade

```typescript
const seniorityLevels = [
  "Intern", "Entry Level", "Associate", "Mid-Senior", 
  "Senior", "Manager", "Director", "VP", "C-Level"
]
```

### 4.7 Seção: Empresa

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 31 | Empresas | TagInput + Autocomplete | **SIM** | `current_employer`, `past_employer` | Com filtro temporal |
| 32 | Filtro Temporal Empresa | Dropdown | N/A | Time filter | current_only, past_only, current_past, specific_years, funding_stage |
| 33 | Anos Específicos | Range | N/A | `company_years_start/end` | Período de atuação |
| 34 | Empresas Excluídas | TagInput | N/A | `exclude_current_employer`, `exclude_companies` | Exclusão |
| 35 | Setores/Indústrias | TagInput | **SIM** | `industries` | Busca semântica LLM |
| 36 | Tags da Empresa | TagInput | N/A | `company_tags` | Características |
| 37 | Sede da Empresa | TagInput | N/A | `company_hq_locations` | Localização HQ |
| 38 | Porte da Empresa | Chips | N/A | `company_sizes` | 8 faixas |
| 39 | Fundada Após | Number | N/A | `company_founded_after` | Ano de fundação |
| 40 | Estágio de Funding | Chips | N/A | `funding_stages` | Seed a IPO |

#### Portes de Empresa

```typescript
const companySizes = [
  { value: "1-10", label: "1-10" },
  { value: "11-50", label: "11-50" },
  { value: "51-200", label: "51-200" },
  { value: "201-500", label: "201-500" },
  { value: "501-1000", label: "501-1K" },
  { value: "1001-5000", label: "1K-5K" },
  { value: "5001-10000", label: "5K-10K" },
  { value: "10001+", label: "10K+" }
]
```

#### Estágios de Funding

```typescript
const fundingStages = [
  "Pre-Seed", "Seed", "Series A", "Series B", "Series C", 
  "Series D", "Series E+", "Private Equity", "IPO", "Acquired"
]
```

### 4.8 Seção: Habilidades

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 41 | Skills Técnicas | TagInput + Pin | **SIM** | `skills` | Obrigatórias vs Nice-to-have |
| 42 | Áreas de Expertise | TagInput | **SIM** | `expertise` | Domínios de conhecimento |

### 4.9 Seção: Formação

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 43 | Universidades | TagInput + Presets | N/A | `universities` | Com presets de top universidades |
| 44 | Universidades Excluídas | TagInput | N/A | `excluded_universities` | Exclusão |
| 45 | Localização Universidade | TagInput | N/A | `university_locations` | País/região |
| 46 | Grau Acadêmico | Dropdown | N/A | `degree` | Bachelor, Master, PhD, etc. |
| 47 | Modo Grau | Toggle | N/A | `degreeRequirementMode` | regular \| nested |
| 48 | Áreas de Estudo | TagInput | **SIM** | `fields_of_study` | Cursos/majors |
| 49 | Modo Áreas de Estudo | Toggle | N/A | `fieldsOfStudyMode` | regular \| nested |
| 50 | Ano Formatura (Min) | Number | N/A | `graduation_year_min` | Filtro temporal |
| 51 | Ano Formatura (Max) | Number | N/A | `graduation_year_max` | Filtro temporal |

#### Graus Acadêmicos

```typescript
const degrees = [
  "High School", "Associate", "Bachelor's", "Master's", 
  "MBA", "PhD", "MD", "JD", "Other"
]
```

### 4.10 Seção: Idiomas

| # | Campo | Tipo | Busca Semântica | API Parameter | Descrição |
|---|-------|------|-----------------|---------------|-----------|
| 52 | Idiomas | TagInput | N/A | `languages` | Lista de idiomas |
| 53 | Nível de Proficiência | Dropdown | N/A | `proficiency_level` | Mínimo requerido |

#### Níveis de Proficiência

```typescript
const proficiencyLevels = [
  { value: "any", label: "Qualquer Nível" },
  { value: "basic", label: "Básico" },
  { value: "conversational", label: "Conversacional" },
  { value: "professional", label: "Profissional" },
  { value: "native", label: "Nativo/Fluente" }
]
```

---

## 5. Dicionário de Dados - Definições Detalhadas dos Campos

Esta seção apresenta a definição completa de cada campo, incluindo conceito, metodologia de cálculo, fonte do dado e regras de negócio.

### 5.1 Campos Gerais

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Tempo de Experiência Mínimo** | Quantidade mínima de anos de experiência profissional do candidato | Calculado como: `(Data Atual) - (Data de Início da Primeira Experiência Profissional)`. Considera apenas experiências com data de início válida. Arredonda para anos completos. | LinkedIn (work_history), Currículo PDF parseado, Cadastro manual | Inclui estágios/trainee se cadastrados como experiência. Períodos de gap não são subtraídos. Experiências simultâneas não são duplicadas. |
| **Tempo de Experiência Máximo** | Quantidade máxima de anos de experiência profissional do candidato | Mesma metodologia do mínimo. Usado para excluir candidatos muito seniores para a vaga | LinkedIn, Currículo, Cadastro | Filtro "até X anos" é inclusivo (≤). Útil para vagas junior/pleno que não comportam seniors. |
| **Ocultar Perfis Visualizados** | Remove da busca candidatos já visualizados pelo recrutador | Cruza IDs da busca com tabela `viewed_candidates` filtrando por `user_id` do recrutador | Tabela `viewed_candidates` do banco local | Escopo configurável: apenas eu, minha equipe, minha empresa. Período: 7d, 30d, 90d, sempre. |
| **Escopo de Visualização** | Define quem são os "visualizadores" considerados | Consulta `viewed_candidates` filtrando por: `user_id` (individual), `team_id` (equipe), `company_id` (empresa) | Banco de dados local | "Apenas eu" = `user_id` atual. "Minha equipe" = todos `user_id` do mesmo `team_id`. "Minha empresa" = todos do `company_id`. |
| **Período de Visualização** | Janela temporal para considerar visualizações | Filtra `viewed_at >= (NOW() - período)` | Tabela `viewed_candidates.viewed_at` | 7 dias, 30 dias, 90 dias, ou "sempre" (sem filtro de data). |

### 5.2 Campos de Localização

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Localização** | Cidade, estado ou país onde o candidato reside atualmente | Geocodificação do endereço informado ou extraído do LinkedIn | LinkedIn (`location`), Cadastro, Currículo parseado | Aceita múltiplas localidades (OR). Formato: "Cidade, Estado, País" ou parcial. Normalizado para padrão ISO. |
| **Raio de Busca** | Distância máxima do centro da localização selecionada | Cálculo de distância geodésica (Haversine) entre coordenadas do candidato e centro da cidade/região selecionada | Coordenadas geocodificadas da localização | Valores: Exato (cidade), 25km, 50km, 100km, 250km. "Exato" considera apenas mesma cidade. |
| **Países** | Filtro por país de residência | Match exato com código ISO ou nome do país normalizado | Campo `location_country` do perfil | Aceita múltiplos países (OR). Códigos ISO 3166-1 alpha-2 (BR, US, PT). |
| **Fuso Horário** | Timezone do candidato para compatibilidade de horário | Inferido da localização ou declarado explicitamente | Geocodificação ou campo `timezone` | Formato IANA (America/Sao_Paulo). Útil para times remotos globais. |
| **Localizações Anteriores** | Cidades/países onde o candidato já residiu | Extraído do histórico de experiências (localização das empresas) + campo específico | LinkedIn (histórico de empregos), Cadastro | Período configurável: qualquer momento, últimos 5 anos, últimos 10 anos. Indica mobilidade prévia. |

### 5.3 Campos de Cargo e Função

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Cargo** | Título profissional do candidato | Match textual + expansão semântica via LLM (sinônimos, variações) | LinkedIn (`headline`, `current_title`), Currículo | Busca semântica expande: "Backend Developer" → "Desenvolvedor Backend", "Back-End Engineer", "Server-Side Developer". |
| **Escopo do Cargo** | Define se busca cargo atual, recente ou histórico | Filtra por: `is_current=true` (atual), `end_date >= 2 anos` (recente), qualquer (histórico) | Campo `is_current` e `end_date` do work_history | "Apenas atual": experiência ativa. "Atual ou recente": até 2 anos. "Atual ou passado": qualquer momento. |
| **Cargos Anteriores** | Títulos que o candidato já ocupou | Busca em `work_history` onde `is_current=false` | Histórico de experiências | Útil para transição de carreira. Ex: buscar PMs que já foram desenvolvedores. |
| **Nível/Senioridade** | Nível hierárquico do cargo | Classificação baseada em keywords no título + regras de inferência | Análise do título: "Junior", "Pleno", "Senior", "Lead", "Head", "Director", "VP", "C-Level" | Mapeamento: Entry (Junior), Individual Contributor (Pleno/Senior), Manager, Director, VP, CXO. |
| **Função/Área** | Área funcional de atuação | Categorização por análise de título + departamento | LinkedIn, Classificação interna | Exemplos: Engineering, Product, Design, Sales, Marketing, Operations, Finance, HR. |
| **Tempo no Cargo Atual (Mín)** | Tempo mínimo que o candidato está no cargo atual | `(Data Atual) - (Data de Início do Cargo Atual)` | Campo `start_date` da experiência atual | Útil para encontrar candidatos estáveis (>2 anos) ou prontos para mudar (<1 ano). |
| **Tempo no Cargo Atual (Máx)** | Tempo máximo no cargo atual | Mesma metodologia do mínimo | Campo `start_date` da experiência atual | Candidatos com muito tempo (>5 anos) podem indicar estagnação ou alta estabilidade. |
| **Permanência Média em Empregos** | Média de tempo que o candidato fica em cada empresa | `Soma(duração de cada experiência) / Número de experiências` | Histórico completo de `work_history` | Indicador de estabilidade. <1 ano: job hopper. 2-4 anos: média. >5 anos: alta retenção. |

### 5.4 Campos de Empresa

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Empresas** | Empresas onde o candidato trabalha ou trabalhou | Match por nome normalizado + sinônimos corporativos | LinkedIn, Currículo, Base Pearch | Aceita variações: "Google" = "Google LLC" = "Alphabet Inc.". Múltiplas empresas = OR. |
| **Filtro Temporal de Empresa** | Define se busca empresa atual, recente ou histórica | Mesmo mecanismo do escopo de cargo | Campo `is_current` e datas | "Atual": trabalhando agora. "Passado": já trabalhou. "Últimos X anos": filtro temporal. |
| **Anos Específicos** | Período exato em que trabalhou na empresa | Filtra `start_date` e `end_date` dentro do range especificado | Datas do histórico profissional | Intervalo fechado: início ≤ start_date AND end_date ≤ fim (ou is_current se ainda ativo). |
| **Empresas Excluídas** | Empresas que NÃO devem aparecer nos resultados | Blacklist: remove candidatos que trabalham/trabalharam nestas empresas | Mesmo do campo "Empresas" | Útil para: evitar contratar de clientes, parceiros, ou empresas com non-compete. |
| **Excluir DNC (Do Not Contact)** | Remove empresas marcadas como "não contatar" | Cruza com lista DNC do cliente configurada no sistema | Tabela `dnc_companies` por `company_id` | Lista mantida pelo cliente. Geralmente inclui clientes estratégicos, parceiros, fornecedores. |
| **Setor/Indústria** | Segmento de mercado das empresas | Classificação NAICS/GICS + expansão semântica | LinkedIn Company, Crunchbase, classificação interna | Busca semântica: "Fintech" → "Banking", "Payments", "Insurtech", "Cryptocurrency". |
| **Filtro Temporal de Setor** | Define se considera setor da empresa atual ou histórica | Filtra experiências por período antes de extrair setor | Combinação de filtro temporal + classificação | Útil para: "trabalhou em fintech nos últimos 5 anos". |
| **Tags de Empresa** | Características especiais da empresa | Match com taxonomia de tags pré-definida | Base de empresas enriquecida | Exemplos: "Fortune 500", "Unicórnio", "Startup", "Scale-up", "B-Corp", "Remote-first". |
| **Localização da Sede** | País/cidade da sede da empresa | Geocodificação do HQ da empresa | LinkedIn Company, Crunchbase | Útil para: empresas americanas, europeias, etc. independente da localização do funcionário. |
| **Tamanho da Empresa** | Faixa de número de funcionários | Categorização por ranges | LinkedIn Company (`company_size`) | Faixas: 1-10, 11-50, 51-200, 201-500, 501-1000, 1001-5000, 5001-10000, 10000+. |
| **Ano de Fundação (Após)** | Empresas fundadas a partir de determinado ano | Filtra `founded_year >= valor` | Crunchbase, LinkedIn Company | Útil para buscar experiência em startups recentes (fundadas após 2015, por exemplo). |
| **Estágio de Funding** | Fase de investimento da empresa | Match com rounds conhecidos | Crunchbase, PitchBook | Seed, Series A, B, C, D+, Pre-IPO, Public, Bootstrapped. |

### 5.5 Campos de Habilidades

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Habilidades/Skills** | Competências técnicas e comportamentais | Match textual + expansão semântica LLM | LinkedIn Skills, Currículo parseado, Cadastro | Semântico: "React" → "ReactJS", "React.js", "React Native". Operadores: AND (todas), OR (qualquer). |
| **Áreas de Expertise** | Domínios de conhecimento especializado | Classificação por taxonomia + expansão semântica | LinkedIn Skills agrupados, About, Headline | Exemplos: "Machine Learning" expande para "Deep Learning", "NLP", "Computer Vision", "AI/ML". |

### 5.6 Campos de Formação Acadêmica

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Universidades** | Instituições de ensino superior | Match por nome normalizado + sinônimos | LinkedIn Education, Currículo | "USP" = "Universidade de São Paulo". Aceita múltiplas (OR). |
| **Universidades Excluídas** | Instituições a não considerar | Blacklist de universidades | Mesmo do campo "Universidades" | Raramente usado. Pode servir para diversificação de fontes. |
| **Localização da Universidade** | País/região da instituição | Geocodificação da universidade | Base de universidades | "Formado nos EUA", "Universidade europeia". |
| **Grau/Título Acadêmico** | Nível de formação | Match com tipos conhecidos | LinkedIn Education (`degree`) | Bachelor (Graduação), Master (Mestrado), MBA, PhD (Doutorado), Associate, Certificate. |
| **Área de Estudo** | Campo de formação acadêmica | Classificação + expansão semântica | LinkedIn Education (`field_of_study`) | "Ciência da Computação" expande para: "Engenharia de Software", "Sistemas de Informação", "Análise de Sistemas". |
| **Ano de Formatura** | Ano de conclusão do curso | Campo direto ou calculado | LinkedIn Education (`end_date`), Currículo | Filtro: "formados após 2020", "formados entre 2015-2020". |
| **Top Universities** | Indicador de universidade de elite | Flag baseado em rankings internacionais | QS World Rankings, THE Rankings, rankings nacionais | Pearch considera top 100 global + top 10 de cada país. Não é configurável pelo usuário. |

### 5.7 Campos de Idiomas

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Idioma** | Língua que o candidato domina | Match direto | LinkedIn Languages, Currículo, Cadastro | Código ISO 639-1 (pt, en, es, fr, de, etc.) ou nome por extenso. |
| **Nível de Proficiência** | Grau de domínio do idioma | Classificação padronizada | LinkedIn (Basic, Professional, Native), Cadastro | Mapeamento: Basic/Elementary, Intermediate/Professional, Advanced/Fluent, Native/Bilingual. |

### 5.8 Campos de Opções de Busca (PPI)

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Tipo de Busca (Fast/Pro)** | Profundidade da busca na base Pearch | Fast: campos básicos, mais rápido. Pro: todos os campos, mais lento | Configuração de API Pearch | Fast: 1 crédito. Pro: 5 créditos. Pro inclui insights avançados. |
| **Alta Atualização (Freshness)** | Prioriza perfis atualizados recentemente | Ordena/filtra por `last_updated` recente | Metadado Pearch | +2 créditos. Perfis atualizados nos últimos 90 dias têm prioridade. |
| **Filtros Estritos** | Exige match exato nos filtros | Desativa fuzzy matching e expansões | Flag de configuração | Default: flexível. Estrito: exige match 100% nos critérios. |
| **Requer Email** | Apenas candidatos com email disponível | Filtra `has_email = true` | Base Pearch | +1 crédito. Garante contato por email. |
| **Mostrar Emails** | Exibe emails nos resultados | Retorna campo `emails` na resposta | Base Pearch (dado enriquecido) | +2 créditos. Emails pessoais e profissionais quando disponíveis. |
| **Requer Telefone** | Apenas candidatos com telefone disponível | Filtra `has_phone = true` | Base Pearch | +1 crédito. Garante contato por telefone. |
| **Mostrar Telefones** | Exibe telefones nos resultados | Retorna campo `phones` na resposta | Base Pearch (dado enriquecido) | +14 créditos. Alto custo devido à verificação de dados. |
| **Email OU Telefone** | Pelo menos um método de contato | Filtra `has_email = true OR has_phone = true` | Base Pearch | +1 crédito. Garante alguma forma de contato direto. |
| **Apenas Open to Work** | Candidatos sinalizando disponibilidade | Filtra `is_open_to_work = true` | LinkedIn (Open to Work badge), Pearch | Candidatos que ativaram o badge de "Aberto a oportunidades" no LinkedIn. |
| **Incluir Descobertos** | Inclui perfis já encontrados em buscas anteriores | Não filtra pela tabela de `discovered_candidates` | Banco local | Default: true. Se false, só retorna perfis novos nunca vistos. |

### 5.9 Campos de Origem da Busca

| Campo | Definição | Metodologia de Cálculo | Fonte do Dado | Regras de Negócio |
|-------|-----------|------------------------|---------------|-------------------|
| **Origem: Local** | Busca apenas na base interna do cliente | Query no banco PostgreSQL local | Tabela `candidates` | Gratuito. Apenas candidatos já cadastrados/importados. |
| **Origem: Global** | Busca na base Pearch (800M+ perfis) | Chamada API Pearch com filtros convertidos | Pearch AI API | Custo por candidato retornado. Base global de profissionais. |
| **Origem: Híbrida** | Busca local primeiro, complementa com global | 1) Query local 2) Se insuficiente, query Pearch | Combinação local + Pearch | Otimiza custos: usa base própria primeiro, só paga pelo complemento. |

### 5.10 Resumo: Cálculo de Tempo de Experiência

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CÁLCULO DE TEMPO DE EXPERIÊNCIA                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Fórmula:                                                                   │
│  ─────────                                                                  │
│  Anos de Experiência = (Data Atual) - (Data de Início da 1ª Experiência)   │
│                                                                             │
│  Exemplo:                                                                   │
│  ─────────                                                                  │
│  • 1ª experiência iniciou em: Janeiro/2015                                 │
│  • Data atual: Dezembro/2024                                                │
│  • Cálculo: 2024 - 2015 = 9 anos de experiência                            │
│                                                                             │
│  Regras:                                                                    │
│  ─────────                                                                  │
│  ✓ Considera a data de INÍCIO da primeira experiência                      │
│  ✓ Vai até a data ATUAL (hoje), não até o fim da última experiência        │
│  ✓ Períodos de gap NÃO são subtraídos                                      │
│  ✓ Experiências simultâneas NÃO duplicam tempo                             │
│  ✓ Estágios/Trainee são incluídos se cadastrados como experiência          │
│  ✓ Arredonda para anos completos (9.7 anos → 9 anos)                       │
│                                                                             │
│  Fonte de Dados (ordem de prioridade):                                      │
│  ───────────────────────────────────────                                    │
│  1. LinkedIn (work_history parseado)                                        │
│  2. Currículo PDF (extração via NLP)                                        │
│  3. Cadastro manual do candidato                                            │
│  4. Campo years_of_experience declarado                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.11 Resumo: Tempo no Cargo vs Permanência Média

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TEMPO NO CARGO vs PERMANÊNCIA MÉDIA                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEMPO NO CARGO ATUAL                                                       │
│  ─────────────────────                                                      │
│  • Definição: Quanto tempo está no emprego ATUAL                            │
│  • Cálculo: (Hoje) - (Data de início do cargo atual)                       │
│  • Uso: Identificar candidatos prontos para mudança (<1 ano)               │
│         ou muito estáveis (>3 anos)                                         │
│                                                                             │
│  PERMANÊNCIA MÉDIA EM EMPREGOS                                              │
│  ─────────────────────────────                                              │
│  • Definição: Média de tempo em TODOS os empregos                          │
│  • Cálculo: Σ(duração de cada emprego) / nº de empregos                    │
│  • Uso: Identificar padrão de comportamento                                 │
│                                                                             │
│  Interpretação:                                                             │
│  ───────────────                                                            │
│  < 1 ano:    Job hopper (alta rotatividade)                                │
│  1-2 anos:   Abaixo da média                                                │
│  2-4 anos:   Média de mercado                                               │
│  4-6 anos:   Acima da média (boa estabilidade)                             │
│  > 6 anos:   Alta retenção (pode indicar resistência a mudanças)           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Sistema de Busca Semântica (LLM-Powered)

### 5.1 Campos com Busca Semântica

| Campo | Endpoint API | Domínio | Exemplos de Expansão |
|-------|--------------|---------|----------------------|
| Skills | `/api/v1/semantic-search/skills` | skills | React → ReactJS, Next.js, Redux |
| Cargos | `/api/v1/semantic-search/job-titles` | job_titles | Backend Dev → Back-End Engineer |
| Funções | `/api/v1/semantic-search/roles` | roles | Engineering → Development, DevOps |
| Setores | `/api/v1/semantic-search/industries` | industries | Fintech → Banking, Payments |
| Expertise | `/api/v1/semantic-search/expertise` | expertise | ML → Data Science, AI |
| Áreas de Estudo | `/api/v1/semantic-search/fields-of-study` | fields_of_study | CS → Software Engineering |
| Empresas | `/api/v1/semantic-search/companies` | companies | Nubank → Inter, C6 Bank |

### 5.2 Arquitetura da Busca Semântica

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
├─────────────────────────────────────────────────────────────────┤
│  useSemanticSearch Hook                                          │
│  ├── debounce: 400ms                                             │
│  ├── SWR caching                                                 │
│  └── Specialized helpers (useSemanticSkills, etc.)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
├─────────────────────────────────────────────────────────────────┤
│  /api/v1/semantic-search/{domain}                                │
│  ├── Redis Cache Check (TTL 10min)                               │
│  ├── Static Taxonomy Fallback                                    │
│  └── Gemini 1.5 Flash API Call                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Google Gemini 1.5 Flash                        │
├─────────────────────────────────────────────────────────────────┤
│  Semantic expansion with domain-specific prompts                 │
│  Target: P95 < 300ms                                             │
│  Cost: ~$0.0001/query                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Hook Frontend: useSemanticSearch

```typescript
// plataforma-lia/src/hooks/useSemanticSearch.ts

interface UseSemanticSearchOptions {
  domain: SemanticDomain  // 'skills' | 'job_titles' | etc.
  debounceMs?: number     // Default: 400
}

interface SemanticSuggestion {
  term: string
  confidence: number
}

interface UseSemanticSearchReturn {
  suggestions: SemanticSuggestion[]
  isLoading: boolean
  error: string | null
  search: (query: string, existingTerms: string[]) => void
  clearSuggestions: () => void
}

// Uso:
const { suggestions, isLoading, search, clearSuggestions } = 
  useSemanticSearch({ domain: "skills", debounceMs: 400 })
```

### 5.4 Backend: Serviço Semântico

```python
# lia-agent-system/app/services/semantic_search_service.py

class SemanticSearchService:
    def __init__(self):
        self.redis_client = redis.Redis(...)
        self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
    
    async def search(
        self, 
        domain: SemanticDomain, 
        query: str, 
        existing_terms: list[str]
    ) -> list[SemanticSuggestion]:
        # 1. Check Redis cache
        cache_key = f"semantic:{domain}:{query}"
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 2. Check static taxonomy fallback
        static_results = self._check_static_taxonomy(domain, query)
        if static_results:
            return static_results
        
        # 3. Call Gemini API
        prompt = self._build_prompt(domain, query, existing_terms)
        response = await self.gemini_client.generate_content_async(prompt)
        
        # 4. Parse and cache
        suggestions = self._parse_response(response)
        await self.redis_client.setex(cache_key, 600, json.dumps(suggestions))
        
        return suggestions
```

### 5.5 Endpoints da API

```python
# lia-agent-system/app/api/v1/semantic_search.py

@router.post("/skills")
async def search_skills(request: SemanticSearchRequest):
    return await semantic_service.search("skills", request.query, request.existing)

@router.post("/job-titles")
async def search_job_titles(request: SemanticSearchRequest):
    return await semantic_service.search("job_titles", request.query, request.existing)

@router.post("/roles")
async def search_roles(request: SemanticSearchRequest):
    return await semantic_service.search("roles", request.query, request.existing)

@router.post("/industries")
async def search_industries(request: SemanticSearchRequest):
    return await semantic_service.search("industries", request.query, request.existing)

@router.post("/expertise")
async def search_expertise(request: SemanticSearchRequest):
    return await semantic_service.search("expertise", request.query, request.existing)

@router.post("/fields-of-study")
async def search_fields_of_study(request: SemanticSearchRequest):
    return await semantic_service.search("fields_of_study", request.query, request.existing)

@router.post("/companies")
async def search_companies(request: SemanticSearchRequest):
    return await semantic_service.search("companies", request.query, request.existing)
```

---

## 7. Componentes de Input Especializados

### 6.1 SkillsFilterInput

**Arquivo**: `plataforma-lia/src/components/search/SkillsFilterInput.tsx`

**Características**:
- Busca semântica integrada
- Sistema de "pin" para skills obrigatórias vs nice-to-have
- Botão "Find Similar" para expansão via IA
- Autocomplete com taxonomia estática + LLM
- Badge visual diferenciado para skills pinadas

```typescript
interface SkillItem {
  name: string
  isPinned: boolean  // true = obrigatória
}

interface SkillsFilterInputProps {
  value: SkillItem[]
  onChange: (skills: SkillItem[]) => void
  placeholder?: string
}
```

### 6.2 ExpertiseAreasInput

**Arquivo**: `plataforma-lia/src/components/search/ExpertiseAreasInput.tsx`

**Características**:
- Busca semântica por domínio "expertise"
- Lista de expertises populares como fallback
- Botão "Find Similar" para expansão
- 40+ áreas populares pré-definidas

### 6.3 IndustryFilterInput

**Arquivo**: `plataforma-lia/src/components/search/IndustryFilterInput.tsx`

**Características**:
- Busca semântica por domínio "industries"
- Filtro temporal (Atual + Anterior / Apenas Atual)
- Constantes importadas de `industry-constants.ts`
- Suporte bilíngue (EN/PT)

```typescript
type IndustryTimeFilter = 'current_past' | 'current_only'
```

### 6.4 FieldsOfStudyInput

**Arquivo**: `plataforma-lia/src/components/search/FieldsOfStudyInput.tsx`

**Características**:
- Busca semântica por domínio "fields-of-study"
- Modo Regular vs Nested
- 230+ áreas de estudo pré-definidas
- Regular: Qualquer universidade
- Nested: Apenas universidades selecionadas

### 6.5 CompanyFilterInput

**Arquivo**: `plataforma-lia/src/components/search/CompanyFilterInput.tsx`

**Características**:
- Busca semântica por domínio "companies"
- 5 filtros temporais
- Suporte a funding stages
- Suporte a anos específicos

```typescript
type CompanyTimeFilter = 
  | 'current_only'    // Empresa atual
  | 'past_only'       // Empresas anteriores
  | 'current_past'    // Ambos
  | 'specific_years'  // Anos específicos
  | 'funding_stage'   // Por estágio de funding
```

### 6.6 LocationFilterInput

**Arquivo**: `plataforma-lia/src/components/search/LocationFilterInput.tsx`

**Características**:
- Autocomplete de cidades e países
- Integração com RadiusDropdown
- Suporte a timezone
- Presets de localização (Brasil, Latam, US, Europe)

---

## 8. Sistema de Presets

### 7.1 Presets de Cargos

O modal suporta presets globais e customizados para cargos:

```typescript
const globalJobPresets = [
  {
    id: "engineering-backend",
    name: "Backend Engineers",
    description: "Desenvolvedores backend e APIs",
    titles: ["Backend Developer", "Backend Engineer", "API Developer", ...]
  },
  {
    id: "engineering-frontend",
    name: "Frontend Engineers",
    description: "Desenvolvedores frontend e UI",
    titles: ["Frontend Developer", "Frontend Engineer", "UI Developer", ...]
  },
  // ... mais presets
]
```

### 7.2 Presets de Universidades

```typescript
const universityPresets = [
  {
    id: "top-br",
    name: "Top Brasil",
    universities: ["USP", "UNICAMP", "UFRJ", "PUC", "FGV", "ITA", "IME", ...]
  },
  {
    id: "ivy-league",
    name: "Ivy League",
    universities: ["Harvard", "Yale", "Princeton", "Columbia", ...]
  },
  // ... mais presets
]
```

---

## 9. Integração com Pearch API

### 8.1 Conversão de Filtros

A função `convertToPearchFilters` converte os filtros internos para o formato da API Pearch:

```typescript
export function convertToPearchFilters(filters: SearchFilters): {
  customFilters: Record<string, any>
  apiOptions: Record<string, any>
  hideViewedOptions?: {
    enabled: boolean
    scope: HideViewedScope
    period: HideViewedPeriod
  }
}
```

### 8.2 Mapeamento de Campos

| Campo Interno | Campo Pearch API | Notas |
|---------------|------------------|-------|
| `job.titles` | `titles` | Com `title_scope` |
| `job.levels` | `seniority_levels` | Array de níveis |
| `job.roles` | `job_functions` | Áreas funcionais |
| `company.companyItems` | `current_employer` / `past_employer` | Depende do filtro temporal |
| `company.excludedCompanyItems` | `exclude_current_employer` / `exclude_companies` | Exclusão |
| `company.industries` | `industries` | Com filtro temporal |
| `skills.skillItems` | `skills` | Com flag de obrigatório |
| `education.universities` | `universities` | Lista |
| `languages.languages` | `languages` | Lista |

---

## 10. Design System

### 9.1 Cores

| Elemento | Cor | Uso |
|----------|-----|-----|
| Accent Primary | `#60BED1` | Botões, badges ativos, links |
| Accent Hover | `#50a3b8` | Estado hover |
| Background | `#FFFFFF` | Fundo do modal |
| Border | `#E5E7EB` | Bordas de inputs |
| Text Primary | `#1F2937` | Títulos |
| Text Secondary | `#6B7280` | Descrições |
| Warning | `#F59E0B` | Alertas de custo |
| Semantic AI | `#9333EA` | Sugestões LLM |

### 9.2 Tipografia

```typescript
const textStyles = {
  title: "text-lg font-semibold text-gray-800",
  subtitle: "text-sm font-medium text-gray-700",
  description: "text-xs text-gray-500",
  label: "text-xs font-medium text-gray-600"
}
```

### 9.3 Componentes de Badge

```typescript
const badgeStyles = {
  default: "bg-gray-100 text-gray-700 border border-gray-200",
  active: "bg-[#60BED1]/10 border-[#60BED1] text-[#60BED1]",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  semantic: "bg-purple-100 text-purple-600"
}
```

---

## 11. Performance

### 10.1 Otimizações Implementadas

| Técnica | Implementação | Benefício |
|---------|---------------|-----------|
| Debounce | 400ms em inputs | Reduz chamadas API |
| Redis Cache | TTL 10min | Cache de sugestões |
| SWR Cache | Frontend | Reuso de dados |
| Lazy Loading | Componentes | Bundle menor |
| Memoization | useMemo/useCallback | Previne re-renders |
| Static Fallback | Taxonomias locais | Funciona offline |

### 10.2 Métricas Alvo

| Métrica | Alvo | Atual |
|---------|------|-------|
| Time to First Suggestion | < 500ms | ~300ms (cache hit) |
| Semantic Search P95 | < 300ms | ~250ms |
| Modal Open | < 100ms | ~50ms |
| Filter Apply | < 200ms | ~100ms |

---

## 12. Destinos de Salvamento

O modal oferece 3 destinos para salvar buscas:

```typescript
const saveDestinations = [
  { 
    key: "talent_funnel", 
    label: "Funil de Talentos", 
    description: "Adicionar candidatos ao funil de uma vaga",
    icon: FolderOpen 
  },
  { 
    key: "search_history", 
    label: "Histórico de Buscas", 
    description: "Salvar automaticamente no histórico",
    icon: History 
  },
  { 
    key: "saved_searches", 
    label: "Buscas Salvas", 
    description: "Favoritar para reutilizar depois",
    icon: Bookmark 
  }
]
```

---

## 13. Navegação Lateral

O modal possui navegação lateral com scroll sync:

```typescript
const sidebarCategories = [
  { key: "searchSource", label: "Origem", icon: Search },
  { key: "ppiOptions", label: "Opções de Busca", icon: Zap },
  { key: "general", label: "Geral", icon: Settings },
  { key: "profile", label: "Perfil", icon: UserCheck },
  { key: "locations", label: "Localização", icon: MapPin },
  { key: "job", label: "Cargo", icon: Briefcase },
  { key: "company", label: "Empresa", icon: Building2 },
  { key: "skills", label: "Habilidades", icon: Code },
  { key: "education", label: "Formação", icon: GraduationCap },
  { key: "languages", label: "Idiomas", icon: Globe }
]
```

---

## 14. Fluxo de Aplicação de Filtros

```
┌────────────────────────────────────────────────────────────────┐
│ 1. Usuário configura filtros no modal                          │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. Clica "Aplicar Filtros"                                     │
│    - Se busca Global/Híbrida: Mostra dialog de confirmação     │
│    - Se busca Local: Aplica diretamente                        │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. CreditConfirmationDialog                                     │
│    - Mostra custo estimado                                      │
│    - Usuário confirma ou cancela                                │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. convertToPearchFilters()                                     │
│    - Converte para formato Pearch API                           │
│    - Adiciona opções de API                                     │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. searchCandidates()                                           │
│    - Envia para backend                                         │
│    - Backend orquestra Local + Pearch                           │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. Resultados exibidos                                          │
│    - Créditos debitados                                         │
│    - Candidatos mostrados                                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 15. Testes e Validação

### 14.1 Casos de Teste Recomendados

1. **Busca Local**
   - Aplicar filtros básicos
   - Verificar sem custo de créditos

2. **Busca Global**
   - Verificar cálculo de créditos
   - Confirmar dialog de confirmação
   - Validar resultados da Pearch

3. **Busca Semântica**
   - Testar cada domínio (skills, job-titles, etc.)
   - Verificar cache Redis
   - Testar fallback estático

4. **Presets**
   - Aplicar presets de cargos
   - Salvar preset customizado
   - Carregar preset salvo

5. **Filtros Compostos**
   - Combinar múltiplas seções
   - Verificar lógica AND/OR
   - Testar exclusões

---

## 16. Considerações para Migração

### 15.1 Vue.js + Nuxt

Para migrar para Vue.js:
- Converter hooks React para Composables Vue
- Adaptar Radix UI para Headless UI ou similar
- Manter mesma estrutura de API

### 15.2 Ruby on Rails

Para migrar backend para Rails:
- Manter endpoints REST idênticos
- Implementar serviço de busca semântica
- Configurar Redis cache

---

## 17. Arquivos Chave

| Arquivo | Descrição | Linhas |
|---------|-----------|--------|
| `advanced-filters-modal.tsx` | Componente principal | ~3100 |
| `useSemanticSearch.ts` | Hook de busca semântica | ~150 |
| `semantic_search_service.py` | Serviço backend | ~300 |
| `semantic_search.py` | Endpoints API | ~100 |
| `candidate-search.ts` | API client + cálculo de créditos | ~420 |

---

## 18. Variáveis de Ambiente

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend (.env)
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your-gemini-key
PEARCH_API_KEY=your-pearch-key
```

---

## 19. Changelog

| Data | Versão | Alterações |
|------|--------|------------|
| Dez 2024 | 1.0 | Versão inicial com 42+ campos |
| Dez 2024 | 1.0 | Sistema de busca semântica completo |
| Dez 2024 | 1.0 | Integração Pearch AI |
| Dez 2024 | 1.1 | Atualização para 53 campos + Dicionário de Dados completo |
| Dez 2024 | 1.2 | Dicionário de Dados movido para Seção 5 (logo após Catálogo de Campos) |

---

**Mantido por**: Time de Desenvolvimento WeDo Talent  
**Contato**: tech@wedotalent.com
