# Especificação Técnica: Wizard de Configuração de Vagas

**Plataforma:** WeDo Talent - LIA (Linkedin Intelligence Agent)  
**Versão:** 1.0  
**Última Atualização:** Dezembro 2025

---

## 1. Visão Geral

### 1.1 Propósito

O Wizard de Configuração de Vagas é um fluxo guiado de 8 etapas para criação de vagas de emprego na plataforma WeDo Talent. Ele utiliza inteligência artificial (Claude/Anthropic) para:

- **Extração automática** de critérios a partir de descrições em linguagem natural
- **Sugestão inteligente** de competências técnicas e comportamentais
- **Geração de perguntas de triagem** baseadas na metodologia WSI
- **Calibração de busca** através de feedback do recrutador

### 1.2 Fluxo de 8 Etapas

| Etapa | ID | Título | Descrição |
|-------|-----|--------|-----------|
| 1 | `description` | Descrição Inicial | Input de texto livre ou JD anexado |
| 2 | `basic-info` | Informações Básicas | Cargo, área, gestor, localidade, modelo de trabalho |
| 3 | `requirements` | Requisitos Técnicos | Skills técnicas com nível e categoria |
| 4 | `behavioral` | Competências Comportamentais | Competências com peso e justificativa |
| 5 | `salary` | Remuneração | Faixa salarial, bônus e benefícios |
| 6 | `wsi-questions` | Perguntas de Triagem | Perguntas WSI para pré-qualificação |
| 7 | `review` | Revisão Final | Resumo com EVP, cultura e valores |
| 8 | `calibration` | Calibração de Perfis | Avaliação de candidatos para refinamento |

---

## 2. Detalhamento das Etapas

### 2.1 Etapa 1: Descrição Inicial (`description`)

**Stage Config:**
```typescript
{
  id: 'description',
  title: 'Descrição Inicial',
  subtitle: 'Etapa 1 de 8',
  panelTitle: 'Critérios Detectados'
}
```

**Campos de Entrada:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| Texto descritivo | `string` | Sim | Descrição em linguagem natural da vaga |
| Anexo JD | `File` | Não | Documento PDF/DOCX com Job Description |

**Processamento IA:**
- Claude analisa o texto e extrai critérios estruturados
- Popula automaticamente o objeto `DetectedCriteria`
- Identifica cargo, área, competências, localização, modelo de trabalho

**Impacto na Plataforma:**
- Define base para todas as etapas subsequentes
- Alimenta suggestions nas próximas telas

---

### 2.2 Etapa 2: Informações Básicas (`basic-info`)

**Stage Config:**
```typescript
{
  id: 'basic-info',
  title: 'Informações Básicas',
  subtitle: 'Etapa 2 de 8',
  panelTitle: 'Informações Básicas'
}
```

**Campos:**
| Campo | Tipo | Obrigatório | Validação | Descrição |
|-------|------|-------------|-----------|-----------|
| `cargo` | `string` | Sim | min: 3 chars | Título do cargo |
| `area` | `string` | Sim | Seleção de lista | Departamento/área da vaga |
| `gestor` | `string` | Sim | Email válido | Gestor responsável pela vaga |
| `localidade` | `string` | Sim | - | Cidade/Estado ou "Remoto" |
| `modeloTrabalho` | `enum` | Sim | Presencial/Híbrido/Remoto | Modelo de trabalho |
| `tipoContrato` | `enum` | Sim | CLT/PJ/Temporário/Estágio | Tipo de contratação |

**Processamento IA:**
- Pré-preenchimento baseado na descrição inicial
- Cruzamento com dados cadastrados da empresa (áreas, gestores)
- Sugestão de senioridade baseada em keywords

**Impacto na Plataforma:**
- **Candidate Search:** Filtros de localidade e modelo de trabalho
- **Reports/Dashboards:** Métricas por departamento
- **Recruitment Journey:** Definição de SLAs por área

---

### 2.3 Etapa 3: Requisitos Técnicos (`requirements`)

**Stage Config:**
```typescript
{
  id: 'requirements',
  title: 'Requisitos Técnicos',
  subtitle: 'Etapa 3 de 8',
  panelTitle: 'Requisitos Técnicos'
}
```

**Interface:**
```typescript
interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool'
}
```

**Campos por Skill:**
| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `name` | `string` | min: 2 chars | Nome da tecnologia |
| `level` | `enum` | Básico/Intermediário/Avançado | Nível de proficiência esperado |
| `required` | `boolean` | - | Obrigatório vs Desejável |
| `category` | `enum` | language/framework/database/tool | Categoria da skill |

**Categorias Disponíveis:**
- `language`: Python, Java, JavaScript, TypeScript, Go, Rust, etc.
- `framework`: React, Angular, Django, FastAPI, Spring, etc.
- `database`: PostgreSQL, MongoDB, Redis, Elasticsearch, etc.
- `tool`: Docker, Kubernetes, Git, Jenkins, Terraform, etc.

**Processamento IA:**
- Extração automática de tecnologias da descrição
- Sugestão de skills complementares baseada em patterns de mercado
- Categorização automática por tipo

**Impacto na Plataforma:**
- **Nota LIA - Technical Match:** Pontuação baseada em match de skills
- **Candidate Search:** Filtros técnicos na busca
- **WSI Triagem:** Perguntas técnicas específicas

---

### 2.4 Etapa 4: Competências Comportamentais (`behavioral`)

**Stage Config:**
```typescript
{
  id: 'behavioral',
  title: 'Competências Comportamentais',
  subtitle: 'Etapa 4 de 8',
  panelTitle: 'Competências Comportamentais'
}
```

**Interface:**
```typescript
interface BehavioralCompetency {
  id: string
  name: string
  weight: number // 1-5
  justification: string
  enabled: boolean
}
```

**Campos por Competência:**
| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `name` | `string` | Lista predefinida | Nome da competência |
| `weight` | `number` | 1-5 | Peso na avaliação (1=baixo, 5=crítico) |
| `justification` | `string` | max: 500 chars | Justificativa para o peso |
| `enabled` | `boolean` | - | Competência ativa/inativa |

**Competências Padrão (Big Five Mapping):**
| Competência | Big Five Dimension | Weight Default |
|-------------|-------------------|----------------|
| Comunicação Eficaz | Extraversion | 4 |
| Resolução de Problemas | Openness | 5 |
| Adaptabilidade | Openness | 4 |
| Trabalho em Equipe | Agreeableness | 4 |
| Proatividade | Conscientiousness | 3 |
| Liderança | Extraversion | 3 |
| Resiliência | Stability | 4 |
| Foco em Resultados | Conscientiousness | 4 |

**Processamento IA:**
- Sugestão baseada no perfil da vaga e cultura da empresa
- Cálculo de fit cultural usando Big Five organizacional
- Justificativas pré-preenchidas contextualizadas

**Impacto na Plataforma:**
- **Nota LIA - Behavioral Fit:** Pontuação ponderada pelos weights
- **WSI Triagem:** Perguntas comportamentais baseadas em CBI
- **Culture Fit Score:** Match com Big Five da empresa

---

### 2.5 Etapa 5: Remuneração (`salary`)

**Stage Config:**
```typescript
{
  id: 'salary',
  title: 'Remuneração',
  subtitle: 'Etapa 5 de 8',
  panelTitle: 'Salário e Benefícios'
}
```

**Interface:**
```typescript
interface SalaryInfo {
  minSalary: string
  maxSalary: string
  minBonus: string
  maxBonus: string
  bonusCriteria: string
  benefits: Benefit[]
}

interface Benefit {
  id: string
  name: string
  value?: string
  enabled: boolean
}
```

**Campos:**
| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `minSalary` | `string` | Numérico, formato BRL | Salário mínimo da faixa |
| `maxSalary` | `string` | Numérico, >= minSalary | Salário máximo da faixa |
| `minBonus` | `string` | Numérico | Bônus mínimo (%) |
| `maxBonus` | `string` | Numérico | Bônus máximo (%) |
| `bonusCriteria` | `string` | max: 500 chars | Critérios para bônus |
| `benefits` | `Benefit[]` | - | Lista de benefícios |

**Benefícios Padrão:**
- Vale Refeição/Alimentação
- Plano de Saúde
- Plano Odontológico
- Seguro de Vida
- Gympass/Wellhub
- Day Off Aniversário
- PLR/PPR
- Auxílio Home Office

**Processamento IA:**
- Sugestão de faixa baseada em mercado e senioridade
- Benefícios pré-carregados do setup da empresa
- Comparativo com vagas similares

**Impacto na Plataforma:**
- **Candidate Search:** Filtro por pretensão salarial
- **Job Posting:** Exibição na descrição pública
- **Reports:** Análise de competitividade salarial

---

### 2.6 Etapa 6: Perguntas de Triagem WSI (`wsi-questions`)

**Stage Config:**
```typescript
{
  id: 'wsi-questions',
  title: 'Perguntas de Triagem',
  subtitle: 'Etapa 6 de 8',
  panelTitle: 'Perguntas de Triagem WSI'
}
```

**Interface:**
```typescript
interface WSIQuestion {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean
  options?: string[]
  expectedAnswer?: string | number | boolean
  correctOptionIndex?: number
}

interface WSIQuestionCandidate extends WSIQuestion {
  selected: boolean
  batch: number
  isWSI?: boolean
  competency?: string
  framework?: string
  category?: 'autodeclaracao_contexto' | 'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
}
```

**Tipos de Pergunta:**
| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `open` | Resposta dissertativa | "Descreva um projeto desafiador..." |
| `yes-no` | Binário Sim/Não | "Você tem disponibilidade para viagens?" |
| `numeric` | Valor numérico | "Qual sua pretensão salarial?" |
| `multiple-choice` | Múltipla escolha | "Qual seu nível de inglês?" |

**Categorias WSI:**
| Categoria | Framework | Descrição |
|-----------|-----------|-----------|
| `autodeclaracao_contexto` | CBI | Auto-declaração com contexto |
| `micro_case` | Bloom | Caso prático simplificado |
| `situacional` | STAR | Pergunta situacional comportamental |
| `fit` | Big Five | Avaliação de fit cultural |
| `autodeclaracao` | Dreyfus | Auto-avaliação de proficiência |

**Processamento IA:**
- Geração automática baseada em competências selecionadas
- Aplicação da Metodologia WSI (Big Five + Bloom + Dreyfus + CBI)
- Perguntas padrão da empresa + específicas da vaga

**Impacto na Plataforma:**
- **WSI Triagem:** Enviadas via WhatsApp para candidatos
- **Nota LIA:** Análise de respostas para scoring
- **Candidate Ranking:** Pré-qualificação automática

---

### 2.7 Etapa 7: Revisão Final (`review`)

**Stage Config:**
```typescript
{
  id: 'review',
  title: 'Revisão Final',
  subtitle: 'Etapa 7 de 8',
  panelTitle: 'Resumo da Vaga'
}
```

**Componentes Exibidos:**
1. **Resumo da Vaga:** Todos os campos preenchidos
2. **Apresentação da Empresa:** Sobre, missão, visão
3. **EVP (Employee Value Proposition):** Bullets de proposta de valor
4. **Valores e Cultura:** Valores corporativos e descrição cultural
5. **Desafios da Posição:** Principais responsabilidades

**Processamento IA:**
- Compilação automática de dados da empresa
- Geração de texto de apresentação
- EVP dinâmico baseado em benefícios e cultura

**Impacto na Plataforma:**
- **Job Posting:** Texto publicado no ATS
- **Candidate Experience:** Primeira impressão da vaga
- **Employer Branding:** Consistência de comunicação

---

### 2.8 Etapa 8: Calibração de Perfis (`calibration`)

**Stage Config:**
```typescript
{
  id: 'calibration',
  title: 'Calibração de Perfis',
  subtitle: 'Etapa 8 de 8',
  panelTitle: 'Calibração LIA'
}
```

**Interface:**
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
  highlights: {
    icon: string
    label: string
    value: string
  }[]
  experiences: CalibrationCandidateExperience[]
  educationHistory: CalibrationCandidateEducation[]
  skillMap: {
    category: string
    skills: string[]
  }[]
  languages: string[]
  additionalSkills: string[]
  matchCriteria: CalibrationMatchCriteria[]
  overallScore: number
  averageTenure: string
  currentTenure: string
  totalExperience: string
}

interface CalibrationCandidateExperience {
  id: string
  company: string
  role: string
  period: string
  duration: string
  location?: string
  isPromotion?: boolean
  skills: string[]
}

interface CalibrationCandidateEducation {
  id: string
  institution: string
  degree: string
  field: string
  period: string
}

interface CalibrationMatchCriteria {
  id: string
  criteria: string
  isMatch: boolean
  explanation: string
  importance: 1 | 2  // 1 = Importante, 2 = Crítico
}
```

**Fluxo de Calibração:**
1. LIA apresenta 3 candidatos da base de talentos
2. Recrutador avalia cada candidato (Aprovado/Rejeitado)
3. Recrutador pode ajustar match criteria
4. Feedback alimenta modelo de busca

**Processamento IA:**
- Busca inicial na base de talentos da empresa
- Fallback para base global se necessário
- Refinamento de query baseado em feedback

**Impacto na Plataforma:**
- **Candidate Search:** Query refinada para buscas futuras
- **ML Model:** Training data para matching
- **Search Quality:** Melhoria contínua de resultados

---

## 3. Arquitetura de Integração com IA

### 3.1 Apify Services

**Arquivo:** `lia-agent-system/app/services/apify_service.py`

#### LinkedIn Scraper
```python
LINKEDIN_ACTOR_ID = "voyager/linkedin-company-profile-scraper"
```

**Dados Extraídos:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `description` | `string` | Descrição da empresa |
| `tagline` | `string` | Slogan/tagline |
| `specialties` | `string[]` | Especialidades |
| `industries` | `string[]` | Indústrias de atuação |
| `company_size` | `string` | Faixa de funcionários |
| `headquarters` | `string` | Sede principal |

#### Glassdoor Scraper
```python
GLASSDOOR_ACTOR_ID = "bebity/glassdoor-scraper"
```

**Dados Extraídos:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `rating` | `number` | Rating geral (1-5) |
| `reviews` | `object[]` | Avaliações de funcionários |
| `culture_keywords` | `string[]` | Keywords de cultura |
| `pros_cons` | `object` | Prós e contras |

---

### 3.2 Company Scraper Service

**Arquivo:** `lia-agent-system/app/services/company_scraper_service.py`

#### Website Crawler
```python
APIFY_ACTOR_ID = "apify~website-content-crawler"
```

**Configuração:**
| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| Max Pages | 15 | Limite de páginas |
| Max Depth | 2 | Profundidade de crawl |
| Timeout | 120s | Timeout por requisição |

#### Culture Page Patterns
```python
CULTURE_PAGE_PATTERNS = [
    r'/about', r'/sobre', r'/quem-somos', r'/who-we-are',
    r'/careers', r'/carreiras', r'/trabalhe-conosco',
    r'/jobs', r'/vagas',
    r'/culture', r'/cultura', r'/our-culture', r'/nossa-cultura',
    r'/values', r'/valores',
    r'/mission', r'/missao',
    r'/company', r'/empresa',
    r'/team', r'/time', r'/equipe',
    r'/life-at', r'/vida-na'
]
```

#### LinkedIn Company Scraper
```python
LINKEDIN_ACTOR_ID = "curious_coder~linkedin-company-scraper"
```

---

### 3.3 Culture Analyzer Service

**Arquivo:** `lia-agent-system/app/services/culture_analyzer_service.py`

**LLM Provider:** Claude (Anthropic)

#### Dados Extraídos

**Cultura Organizacional:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `mission` | `string` | Missão da empresa |
| `vision` | `string` | Visão de futuro |
| `values` | `string[]` | Valores corporativos |
| `evp_bullets` | `string[]` | Employee Value Proposition |
| `core_competencies` | `string[]` | Competências valorizadas |
| `culture_description` | `string` | Descrição da cultura |

**Informações da Empresa:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `industry` | `string` | Setor de atuação |
| `employee_count` | `number` | Número de funcionários |
| `company_size` | `enum` | Startup/PME/Enterprise |
| `headquarters` | `string` | Sede principal |
| `locations` | `string[]` | Outras localidades |
| `founded_year` | `number` | Ano de fundação |

**Ambiente de Trabalho:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `work_model` | `enum` | Remoto/Híbrido/Presencial |
| `growth_opportunities` | `string` | Oportunidades de crescimento |
| `team_dynamics` | `string` | Dinâmica de equipes |
| `leadership_style` | `string` | Estilo de liderança |

**Responsabilidade Social:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `dei_initiatives` | `string` | Iniciativas de D&I |
| `sustainability` | `string` | Práticas sustentáveis |
| `social_impact` | `string` | Impacto social |

**Tecnologia:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `tech_stack` | `string[]` | Stack tecnológico |
| `engineering_culture` | `string` | Cultura de engenharia |

#### Big Five Organizational Profile

```typescript
interface BigFiveOrganizational {
  openness: number        // 0-100 - Inovação, experimentação
  conscientiousness: number // 0-100 - Processos, qualidade
  extraversion: number    // 0-100 - Colaboração, networking
  agreeableness: number   // 0-100 - Suporte, empatia
  stability: number       // 0-100 - Previsibilidade, segurança
}
```

**Interpretação dos Scores:**

| Dimensão | Score Alto (>70) | Score Baixo (<40) |
|----------|------------------|-------------------|
| Openness | Startup inovadora | Empresa tradicional |
| Conscientiousness | Foco em processos | Ambiente flexível |
| Extraversion | Cultura colaborativa | Trabalho individual |
| Agreeableness | Suporte e mentoria | Competitividade |
| Stability | Ambiente estável | Alta volatilidade |

---

## 4. Diagramas de Fluxo de Dados

### 4.1 Fluxo: Descrição → Critérios Detectados

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   User Input    │────▶│   Claude API     │────▶│ DetectedCriteria  │
│  (Texto/Anexo)  │     │   (Extraction)   │     │     Object        │
└─────────────────┘     └──────────────────┘     └───────────────────┘
        │                        │                        │
        │                        ▼                        ▼
        │               ┌──────────────────┐     ┌───────────────────┐
        │               │  NLP Processing  │     │   Pre-fill Forms  │
        │               │  - Entity Recog  │     │   - basic-info    │
        │               │  - Skill Extract │     │   - requirements  │
        │               │  - Location Parse│     │   - behavioral    │
        │               └──────────────────┘     └───────────────────┘
```

### 4.2 Fluxo: Company URL → Culture Profile

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Company URL    │────▶│   Apify Actors   │────▶│   Raw Content     │
│  (Website)      │     │  - Web Crawler   │     │   (HTML/Text)     │
└─────────────────┘     │  - LinkedIn      │     └───────────────────┘
                        └──────────────────┘              │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│ Company Profile │◀────│   Claude API     │◀────│ Content Analysis  │
│  (Structured)   │     │ (Culture Prompt) │     │  - Culture Pages  │
│  - Big Five     │     │                  │     │  - About/Values   │
│  - EVP          │     │                  │     │  - LinkedIn Data  │
│  - Values       │     │                  │     │                   │
└─────────────────┘     └──────────────────┘     └───────────────────┘
```

### 4.3 Fluxo: Competências → Perguntas WSI

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│ Technical Skills│────▶│  WSI Question    │────▶│ Generated         │
│ + Behavioral    │     │  Generator       │     │ Questions         │
│ Competencies    │     │                  │     │                   │
└─────────────────┘     └──────────────────┘     └───────────────────┘
        │                        │                        │
        │                        ▼                        ▼
        │               ┌──────────────────┐     ┌───────────────────┐
        │               │  Frameworks:     │     │ Question Types:   │
        │               │  - Big Five      │     │ - autodeclaracao  │
        │               │  - Bloom         │     │ - micro_case      │
        │               │  - Dreyfus       │     │ - situacional     │
        │               │  - CBI           │     │ - fit             │
        │               └──────────────────┘     └───────────────────┘
```

### 4.4 Fluxo: Calibração → Refinamento de Busca

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│ Calibration     │────▶│  Feedback        │────▶│ Search Query      │
│ Feedback        │     │  Processing      │     │ Refinement        │
│ (3 candidates)  │     │                  │     │                   │
└─────────────────┘     └──────────────────┘     └───────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│ User Actions:   │     │ ML Processing:   │     │ Refined Search:   │
│ - Approve       │     │ - Weight adjust  │     │ - Better ranking  │
│ - Reject        │     │ - Pattern learn  │     │ - Relevant skills │
│ - Criteria edit │     │ - Preference     │     │ - Culture match   │
└─────────────────┘     └──────────────────┘     └───────────────────┘
```

---

## 5. Matriz de Impacto na Plataforma

### 5.1 Campos → Funcionalidades

| Campo/Etapa | Nota LIA | WSI Triagem | Candidate Search | Recruitment Journey | Reports |
|-------------|----------|-------------|------------------|---------------------|---------|
| **cargo** | - | ✓ | ✓ | ✓ | ✓ |
| **area** | - | - | ✓ | ✓ | ✓ |
| **localidade** | - | ✓ | ✓ | - | ✓ |
| **modeloTrabalho** | - | ✓ | ✓ | - | ✓ |
| **technicalSkills** | ✓ Tech Match | ✓ | ✓ | - | ✓ |
| **skillLevel** | ✓ Proficiency | - | ✓ | - | - |
| **behavioralCompetencies** | ✓ Behavioral Fit | ✓ | - | - | - |
| **competencyWeight** | ✓ Weighted Score | ✓ Priority | - | - | - |
| **salaryRange** | - | - | ✓ | - | ✓ |
| **wsiQuestions** | - | ✓ Primary | - | ✓ Automation | - |
| **bigFive** | ✓ Culture Fit | ✓ Fit Q's | - | - | ✓ |
| **calibrationFeedback** | ✓ Refinement | - | ✓ Query | - | - |

### 5.2 Cálculo da Nota LIA

```
Nota LIA = (Technical Match × 0.40) + (Behavioral Fit × 0.35) + (Culture Fit × 0.25)

Technical Match:
  - Skill presence: +base points per required skill
  - Level match: multiplier (Básico: 0.7, Intermediário: 0.85, Avançado: 1.0)
  - Category coverage: bonus for full stack coverage

Behavioral Fit:
  - Competency match: weighted by (1-5 weight)
  - Evidence quality: based on WSI response analysis
  - Consistency: cross-validation of responses

Culture Fit:
  - Big Five alignment: distance calculation
  - Values match: keyword overlap with company values
  - Work model fit: preference alignment
```

---

## 6. API Endpoints

### 6.1 Chat & Conversation

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/backend-proxy/chat` | Enviar mensagem para LIA |
| `POST` | `/api/backend-proxy/chat/with-attachments` | Chat com arquivos anexados |
| `GET` | `/api/backend-proxy/chat/?user_id={id}` | Listar conversas do usuário |
| `GET` | `/api/backend-proxy/chat/?conversation_id={id}` | Histórico da conversa |

### 6.2 WSI (Screening Questions)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/lia/api/wsi/generate-questions` | Gerar perguntas genéricas |
| `POST` | `/api/lia/api/wsi/generate-job-screening-questions` | Gerar perguntas específicas da vaga |
| `POST` | `/api/lia/api/wsi/analyze-response` | Analisar resposta do candidato |
| `POST` | `/api/lia/api/wsi/calculate-wsi` | Calcular score WSI |
| `GET` | `/api/lia/api/wsi/sessions/{sessionId}` | Obter sessão de triagem |
| `GET` | `/api/lia/api/wsi/results/candidate/{candidateId}` | Resultados do candidato |
| `POST` | `/api/lia/api/wsi/start-voice-screening` | Iniciar triagem por voz |
| `GET` | `/api/lia/api/wsi/voice-screening/{sessionId}` | Status da triagem por voz |

### 6.3 Job Vacancies

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/backend-proxy/job-vacancies/` | Listar vagas |
| `POST` | `/api/backend-proxy/job-vacancies` | Criar vaga |
| `GET` | `/api/backend-proxy/job-vacancies/{id}` | Obter vaga |
| `PUT` | `/api/backend-proxy/job-vacancies/{id}` | Atualizar vaga |
| `DELETE` | `/api/backend-proxy/job-vacancies/{id}` | Excluir vaga |
| `PATCH` | `/api/backend-proxy/job-vacancies/{id}/status` | Atualizar status |

### 6.4 Company & Culture

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/backend-proxy/company/analyze-culture` | Analisar cultura via URL |
| `GET` | `/api/backend-proxy/company/culture-profile` | Obter perfil cultural |
| `POST` | `/api/backend-proxy/company/culture-profile/analyze` | Disparar análise |
| `POST` | `/api/backend-proxy/company/culture-profile/analyze-direct` | Análise direta |
| `GET` | `/api/backend-proxy/company/culture-profile/status/{jobId}` | Status da análise |
| `GET` | `/api/backend-proxy/company/culture-values` | Listar valores |
| `POST` | `/api/backend-proxy/company/culture-values` | Criar valor |

### 6.5 Candidate Search

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/backend-proxy/search/candidates` | Buscar candidatos |
| `POST` | `/api/backend-proxy/search/candidates/by-job-description` | Busca por JD |
| `POST` | `/api/backend-proxy/search/calibration/start` | Iniciar calibração |
| `POST` | `/api/backend-proxy/search/calibration/feedback` | Enviar feedback |

---

## 7. Data Schemas (TypeScript Interfaces)

### 7.1 DetectedCriteria

```typescript
interface DetectedCriteria {
  cargo: string | null
  gestorArea: string | null
  competenciasTecnicas: string[]
  competenciasComportamentais: string[]
  senioridadeIdiomas: string | null
  modeloTrabalho: string | null
  localizacao: string | null
  tipoContrato: string | null
  salario: string | null
}
```

### 7.2 BasicInfoFields

```typescript
interface BasicInfoFields {
  cargo: string
  area: string
  gestor: string
  localidade: string
  modeloTrabalho: 'Presencial' | 'Híbrido' | 'Remoto'
  tipoContrato: 'CLT' | 'PJ' | 'Temporário' | 'Estágio'
}
```

### 7.3 TechnicalSkill

```typescript
interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool'
}
```

### 7.4 BehavioralCompetency

```typescript
interface BehavioralCompetency {
  id: string
  name: string
  weight: 1 | 2 | 3 | 4 | 5
  justification: string
  enabled: boolean
}
```

### 7.5 SalaryInfo

```typescript
interface SalaryInfo {
  minSalary: string    // Format: "R$ 10.000"
  maxSalary: string    // Format: "R$ 15.000"
  minBonus: string     // Format: "10" (percentage)
  maxBonus: string     // Format: "20" (percentage)
  bonusCriteria: string
  benefits: Benefit[]
}

interface Benefit {
  id: string
  name: string
  value?: string       // Optional value (e.g., "R$ 1.500/mês")
  enabled: boolean
}
```

### 7.6 WSIQuestion

```typescript
interface WSIQuestion {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean
  options?: string[]                    // For multiple-choice
  expectedAnswer?: string | number | boolean
  correctOptionIndex?: number           // For multiple-choice
}

interface WSIQuestionCandidate extends WSIQuestion {
  selected: boolean
  batch: number
  isWSI?: boolean
  competency?: string
  framework?: 'Big Five' | 'Bloom' | 'Dreyfus' | 'CBI'
  category?: 'autodeclaracao_contexto' | 'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
}
```

### 7.7 CalibrationCandidate

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
  highlights: {
    icon: string
    label: string
    value: string
  }[]
  experiences: CalibrationCandidateExperience[]
  educationHistory: CalibrationCandidateEducation[]
  skillMap: {
    category: string
    skills: string[]
  }[]
  languages: string[]
  additionalSkills: string[]
  matchCriteria: CalibrationMatchCriteria[]
  overallScore: number              // 0-100
  averageTenure: string             // e.g., "2 anos e 3 meses"
  currentTenure: string             // e.g., "1 ano e 6 meses"
  totalExperience: string           // e.g., "8 anos"
}

interface CalibrationCandidateExperience {
  id: string
  company: string
  role: string
  period: string                    // e.g., "Jan 2020 - Presente"
  duration: string                  // e.g., "4 anos"
  location?: string
  isPromotion?: boolean
  skills: string[]
}

interface CalibrationCandidateEducation {
  id: string
  institution: string
  degree: string                    // e.g., "Bacharelado"
  field: string                     // e.g., "Ciência da Computação"
  period: string                    // e.g., "2012 - 2016"
}

interface CalibrationMatchCriteria {
  id: string
  criteria: string                  // e.g., "Python Avançado"
  isMatch: boolean
  explanation: string
  importance: 1 | 2                 // 1 = Importante, 2 = Crítico
}
```

### 7.8 BigFiveProfile

```typescript
interface BigFiveProfile {
  openness: number            // 0-100: Abertura a experiências
  conscientiousness: number   // 0-100: Conscienciosidade
  extraversion: number        // 0-100: Extroversão
  agreeableness: number       // 0-100: Amabilidade
  stability: number           // 0-100: Estabilidade emocional
}
```

### 7.9 CultureProfile

```typescript
interface CultureProfile {
  mission: string | null
  vision: string | null
  values: string[]
  evp_bullets: string[]
  core_competencies: string[]
  culture_description: string | null
  industry: string | null
  employee_count: number | null
  company_size: 'Startup' | 'PME' | 'Enterprise' | null
  headquarters: string | null
  locations: string[]
  founded_year: number | null
  work_model: 'Remoto' | 'Híbrido' | 'Presencial' | null
  growth_opportunities: string | null
  team_dynamics: string | null
  leadership_style: string | null
  dei_initiatives: string | null
  sustainability: string | null
  social_impact: string | null
  tech_stack: string[]
  engineering_culture: string | null
  big_five: BigFiveProfile
  confidence: number          // 0-1: Confidence score da análise
}
```

---

## 8. Considerações de Segurança

### 8.1 Autenticação
- Todas as APIs requerem `Authorization: Bearer {token}`
- Tokens JWT com expiração configurável
- Refresh token para sessões longas

### 8.2 Dados Sensíveis
- Salários são criptografados em repouso
- PII de candidatos com acesso restrito
- Logs sanitizados (sem dados pessoais)

### 8.3 Rate Limiting
- APIs de scraping: 10 req/min
- Chat: 60 msg/min por usuário
- Search: 30 req/min

---

## 9. Referências

- **Metodologia WSI:** `lia-agent-system/training/rag_knowledge/wsi_methodology/`
- **Prompts de IA:** `lia-agent-system/app/agents/prompts/`
- **Frontend Wizard:** `plataforma-lia/src/components/expanded-chat-modal.tsx`
- **Backend Services:** `lia-agent-system/app/services/`
