# DOCUMENTACAO TECNICA - MODULO GESTAO DE VAGAS
# Plataforma LIA - Sistema de Recrutamento com IA

---

## Indice de Fluxos

1. [FLUXO 01: Listagem e Busca de Vagas](#fluxo-01-listagem-e-busca-de-vagas)
2. [FLUXO 02: Criacao Conversacional de Vagas](#fluxo-02-criacao-conversacional-de-vagas)
3. [FLUXO 03: Aprovacao e Publicacao](#fluxo-03-aprovacao-e-publicacao)
4. [FLUXO 04: Kanban de Candidatos](#fluxo-04-kanban-de-candidatos)
5. [FLUXO 05: Triagem e Avaliacao](#fluxo-05-triagem-e-avaliacao)
6. [FLUXO 06: Comunicacao com Candidatos](#fluxo-06-comunicacao-com-candidatos)
7. [FLUXO 07: Agendamento de Entrevistas](#fluxo-07-agendamento-de-entrevistas)
8. [FLUXO 08: Relatorios e Analytics](#fluxo-08-relatorios-e-analytics)
9. [FLUXO 09: Templates de Vagas](#fluxo-09-templates-de-vagas)
10. [FLUXO 10: Assistente LIA de Vagas](#fluxo-10-assistente-lia-de-vagas)

---

# FLUXO 01: LISTAGEM E BUSCA DE VAGAS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Listagem e Busca Inteligente de Vagas**

### O que esse fluxo entrega
Sistema completo de visualizacao, busca avancada e filtragem de vagas com busca semantica por IA, suporte a queries booleanas e multiplas visualizacoes (tabela, cards, portfolio).

### Para qual usuario
- Recrutador
- Tech Recruiter
- Gestor de RH
- Headhunter

### Resultado final esperado
Lista de vagas filtrada e ordenada conforme criterios do usuario, com preview rico de informacoes e acesso rapido ao funil de candidatos.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| JobsPage | Pagina principal de listagem |
| JobSearchBar | Barra de busca com IA |
| JobFiltersPanel | Painel de filtros avancados |
| JobTable | Tabela de vagas com colunas configuraveis |
| JobCard | Card de vaga para visualizacao em grid |
| JobPortfolioView | Visualizacao portfolio/kanban |
| JobQuickFilters | Filtros rapidos inline |
| JobStatusBadge | Badge de status da vaga |
| JobFunnelPreview | Preview mini-funil de candidatos |
| LIAPrompt | Campo de comando para assistente IA |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/jobs | GET | Listar vagas com filtros |
| /api/v1/jobs/search | POST | Busca semantica com IA |
| /api/v1/jobs/filters | GET | Opcoes de filtros disponiveis |
| /api/v1/jobs/{id} | GET | Detalhe da vaga |
| /api/v1/jobs/{id}/funnel | GET | Funil de candidatos da vaga |
| /api/v1/jobs/stats | GET | Estatisticas gerais |

### Dados

| Tabela | Campos |
|--------|--------|
| jobs | id, title, department, status, priority, recruiter_id, manager_id, open_date, deadline, work_model, location, salary_min, salary_max |
| job_filters_cache | user_id, saved_filters, last_used |
| job_search_history | user_id, query, filters, results_count, created_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| VAG-F01 | Listar Vagas | Exibir todas as vagas com paginacao |
| VAG-F02 | Busca Textual | Buscar por titulo, descricao, skills |
| VAG-F03 | Busca Semantica IA | LIA interpreta query natural e extrai entidades |
| VAG-F04 | Busca Booleana | Suporte a AND, OR, NOT em queries |
| VAG-F05 | Filtros por Status | Ativa, Paralisada, Concluida, Rascunho |
| VAG-F06 | Filtros por Prioridade | Alta, Media, Baixa |
| VAG-F07 | Filtros por Departamento | Filtrar por area |
| VAG-F08 | Filtros por Modelo Trabalho | Remoto, Hibrido, Presencial |
| VAG-F09 | Filtros por Recrutador | Vagas do recrutador |
| VAG-F10 | Filtros por Gestor | Vagas do hiring manager |
| VAG-F11 | Filtros por Data | Abertas em X dias, deadline em Y dias |
| VAG-F12 | Filtros por Funil | Vagas sem candidatos, com pipeline cheio |
| VAG-F13 | Filtros por Metricas | NPS baixo, conversao baixa |
| VAG-F14 | Ordenacao Multipla | Por data, candidatos, prioridade, score |
| VAG-F15 | Visualizacao Tabela | Grid de dados configuravel |
| VAG-F16 | Visualizacao Cards | Cards visuais com preview |
| VAG-F17 | Visualizacao Portfolio | Kanban por status |
| VAG-F18 | Preview Lateral | Panel lateral com detalhes |
| VAG-F19 | Acoes em Lote | Selecionar multiplas vagas |
| VAG-F20 | Exportar Lista | CSV/Excel de vagas |

---

## 4. Jornada do Usuario

### Cenario: Recrutador busca vagas urgentes de tecnologia

\`\`\`
1. Usuario acessa pagina de Vagas
2. Ve dashboard com resumo (X ativas, Y urgentes, Z sem candidatos)
3. Digita no campo LIA: "vagas urgentes de dev backend"
4. LIA processa e extrai: urgente=true, departamento=Tecnologia, titulo~Backend
5. Resultados aparecem filtrados
6. Usuario clica em "Visualizar como Cards"
7. Hover em card mostra preview do funil
8. Clica em vaga para ir ao Kanban de candidatos
\`\`\`

### Cenario: Gestor quer ver vagas do seu time

\`\`\`
1. Usuario acessa pagina de Vagas
2. Clica em "Minhas Vagas" (filtro rapido)
3. Sistema filtra por manager_id = usuario logado
4. Ordena por deadline crescente
5. Usuario ve indicadores de saude por vaga
6. Clica em vaga com alerta vermelho
7. Ve detalhes: "30 dias sem contratacao"
\`\`\`

---

## 5. Jornada do Sistema

\`\`\`
INICIO
  |
  v
[Usuario abre /jobs]
  |
  v
[FRONT] Carrega JobsPage
  |
  v
[FRONT] Requisita GET /api/v1/jobs?page=1&limit=20
  |
  v
[BACK] Query jobs com paginacao
  |
  v
[DADOS] SELECT * FROM jobs WHERE company_id = X ORDER BY open_date DESC
  |
  v
[BACK] Retorna lista + meta (total, pages)
  |
  v
[FRONT] Renderiza tabela/cards
  |
  v
[Usuario digita busca: "vagas remotas senior"]
  |
  v
[FRONT] POST /api/v1/jobs/search { query: "vagas remotas senior" }
  |
  v
[BACK] Envia para Claude API (entity extraction)
  |
  v
[IA] Extrai: work_model=remoto, seniority=senior
  |
  v
[BACK] Query com filtros extraidos
  |
  v
[DADOS] SELECT * FROM jobs WHERE work_model = 'remoto' AND seniority = 'senior'
  |
  v
[BACK] Retorna resultados ranqueados
  |
  v
[FRONT] Exibe resultados com pills de filtros ativos
  |
  v
[Usuario clica em vaga]
  |
  v
[FRONT] Navega para /jobs/{id}/kanban
  |
FIM
\`\`\`

---

## 6. Regras de Negocio

### Busca e Filtros

| Regra | Descricao |
|-------|-----------|
| RN-VAG-01 | Busca textual usa match parcial (ILIKE) |
| RN-VAG-02 | Busca semantica extrai ate 5 entidades |
| RN-VAG-03 | Filtros sao combinados com AND |
| RN-VAG-04 | Ordenacao padrao: prioridade DESC, open_date DESC |
| RN-VAG-05 | Cache de busca por 5 minutos |
| RN-VAG-06 | Historico de buscas limitado a 50 ultimas |

### Permissoes

| Regra | Descricao |
|-------|-----------|
| RN-VAG-07 | Recrutador ve todas as vagas da empresa |
| RN-VAG-08 | Gestor ve vagas onde e hiring manager |
| RN-VAG-09 | Admin ve todas as vagas |
| RN-VAG-10 | Recrutador externo ve apenas vagas atribuidas |

### Indicadores

| Regra | Descricao |
|-------|-----------|
| RN-VAG-11 | Vaga urgente: prioridade alta OU urgency_level >= 4 |
| RN-VAG-12 | Vaga parada: >30 dias sem movimentacao no funil |
| RN-VAG-13 | Vaga em risco: <7 dias para deadline e <3 candidatos em entrevista |

---

## 7. Requisitos Tecnicos

### Frontend

\`\`\`typescript
interface JobFilters {
  status: {
    statuses: string[]
    priorities: string[]
    stages: string[]
  }
  dates: {
    openedWithinDays?: number
    closingWithinDays?: number
    noActivityDays?: number
  }
  team: {
    recruiters: string[]
    managers: string[]
    departments: string[]
  }
  position: {
    levels: string[]
    types: string[]
    workModels: string[]
    locations: string[]
  }
  funnel: {
    minCandidates?: number
    maxCandidates?: number
    emptyPipeline?: boolean
    stuckInStage?: boolean
  }
  metrics: {
    minNPS?: number
    maxDaysOpen?: number
    lowConversion?: boolean
  }
  publishing: {
    channels: string[]
    unpublished?: boolean
  }
}
\`\`\`

### Backend

\`\`\`python
class JobSearchRequest(BaseModel):
    query: str
    mode: Literal["semantic", "boolean", "text"] = "semantic"
    filters: Optional[Dict] = None
    page: int = 1
    limit: int = 20
    sort_by: str = "open_date"
    sort_order: Literal["asc", "desc"] = "desc"

class JobResponse(BaseModel):
    id: UUID
    title: str
    department: str
    status: str
    priority: str
    recruiter: RecruiterInfo
    manager: ManagerInfo
    funnel: FunnelStats
    metrics: JobMetrics
    open_date: datetime
    deadline: Optional[datetime]
\`\`\`

### Dados

\`\`\`sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    title VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    description TEXT,
    requirements TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    priority VARCHAR(10) DEFAULT 'media',
    urgency_level INT DEFAULT 3,
    recruiter_id UUID REFERENCES users(id),
    manager_id UUID REFERENCES users(id),
    work_model VARCHAR(20),
    location VARCHAR(100),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    open_date TIMESTAMP,
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_company_status ON jobs(company_id, status);
CREATE INDEX idx_jobs_department ON jobs(department);
CREATE INDEX idx_jobs_recruiter ON jobs(recruiter_id);
\`\`\`

### IA

\`\`\`python
ENTITY_EXTRACTION_PROMPT = """
Extract job search entities from the following query.

Query: {query}

Return JSON with these fields (only include if detected):
- department: string (e.g., "Tecnologia", "Design", "Marketing")
- title_keywords: list[str] (e.g., ["backend", "developer"])
- seniority: string (e.g., "junior", "pleno", "senior")
- work_model: string (e.g., "remoto", "hibrido", "presencial")
- priority: string (e.g., "alta", "media", "baixa")
- status: string (e.g., "ativa", "paralisada")
- location: string (e.g., "Sao Paulo", "Rio de Janeiro")
- urgency: boolean
- has_candidates: boolean
- deadline_soon: boolean
"""
\`\`\`

---

## 8. Roadmap por Fases

### Fase 1: MVP Listagem (Sprint 1)
\`\`\`
[Tabela de vagas]
       |
       v
[Filtros basicos (status, prioridade)]
       |
       v
[Busca textual simples]
       |
       v
[Paginacao]
\`\`\`

### Fase 2: Busca Avancada (Sprint 2)
\`\`\`
[Busca semantica com IA]
       |
       v
[Extracao de entidades]
       |
       v
[Filtros avancados completos]
       |
       v
[Historico de buscas]
\`\`\`

### Fase 3: Visualizacoes (Sprint 2-3)
\`\`\`
[Visualizacao Cards]
       |
       v
[Visualizacao Portfolio]
       |
       v
[Preview lateral]
       |
       v
[Personalizacao de colunas]
\`\`\`

### Fase 4: Acoes em Lote (Sprint 3)
\`\`\`
[Multi-select]
       |
       v
[Acoes em batch]
       |
       v
[Exportacao]
\`\`\`

---

## 9. Mapeamento Tailwind para Vuetify 3

### Componentes de Busca

\`\`\`vue
<!-- JobSearchBar - Vuetify 3 -->
<v-text-field
  v-model="searchQuery"
  prepend-inner-icon="mdi-magnify"
  placeholder="Buscar vagas..."
  variant="outlined"
  density="comfortable"
  hide-details
  clearable
  @keyup.enter="executeSearch"
>
  <template #append-inner>
    <v-btn
      icon="mdi-brain"
      variant="text"
      size="small"
      :loading="isSearching"
      @click="executeSemanticSearch"
    />
  </template>
</v-text-field>

<!-- JobFiltersPanel -->
<v-expansion-panels variant="accordion">
  <v-expansion-panel title="Status e Prioridade">
    <v-expansion-panel-text>
      <v-chip-group
        v-model="selectedStatuses"
        multiple
        column
      >
        <v-chip
          v-for="status in statusOptions"
          :key="status.value"
          :value="status.value"
          filter
          variant="outlined"
        >
          {{ status.label }}
        </v-chip>
      </v-chip-group>
    </v-expansion-panel-text>
  </v-expansion-panel>
</v-expansion-panels>

<!-- JobTable -->
<v-data-table
  :headers="headers"
  :items="jobs"
  :loading="loading"
  :items-per-page="20"
  item-value="id"
  show-select
  hover
  @click:row="openJob"
>
  <template #item.status="{ item }">
    <v-chip
      :color="getStatusColor(item.status)"
      size="small"
      variant="tonal"
    >
      {{ item.status }}
    </v-chip>
  </template>
  
  <template #item.funnel="{ item }">
    <div class="d-flex align-center gap-1">
      <v-chip size="x-small" color="grey">{{ item.funnel.total }}</v-chip>
      <v-icon size="x-small">mdi-arrow-right</v-icon>
      <v-chip size="x-small" color="primary">{{ item.funnel.interview }}</v-chip>
      <v-icon size="x-small">mdi-arrow-right</v-icon>
      <v-chip size="x-small" color="success">{{ item.funnel.hired }}</v-chip>
    </div>
  </template>
</v-data-table>
\`\`\`

---

## 10. Pontos de Uso de IA e Fallbacks

### Pontos de IA

| Ponto | Funcao | Modelo | Latencia |
|-------|--------|--------|----------|
| Busca Semantica | Interpretar query natural | Claude Haiku | 200-500ms |
| Extracao Entidades | Extrair filtros da query | Claude Haiku | 200-500ms |
| Sugestoes de Busca | Autocomplete inteligente | Claude Haiku | 100-300ms |
| Analise de Vagas | Insights sobre portfolio | Claude Sonnet | 1-2s |

### Prompt de Extracao

\`\`\`python
JOB_SEARCH_PROMPT = """
You are an AI assistant for a recruitment platform.
Analyze this job search query and extract structured filters.

Query: {query}

Context:
- Company departments: {departments}
- Available locations: {locations}
- Current job count: {job_count}

Return JSON:
{
  "filters": {...},
  "intent": "search|report|action",
  "confidence": 0.0-1.0,
  "suggestions": ["..."]
}
"""
\`\`\`

### Riscos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Latencia > 2s | Media | Alto | Cache, streaming |
| Extracao incorreta | Media | Medio | Pills editaveis, confirmacao |
| Custo alto por query | Alta | Medio | Cache agressivo, rate limit |
| Timeout IA | Baixa | Alto | Fallback textual |

### Fallbacks

\`\`\`yaml
Se Claude timeout (>5s):
  1. Logar erro com request_id
  2. Usar busca textual simples (ILIKE)
  3. Exibir aviso: "Busca simplificada"
  4. Oferecer retry button

Se extracao falhar:
  1. Usar query completa como titulo match
  2. Nao exibir pills de entidades
  3. Sugerir usar filtros manuais

Se API indisponivel:
  1. Modo offline com filtros manuais apenas
  2. Banner: "Busca inteligente indisponivel"
\`\`\`

---

# FLUXO 02: CRIACAO CONVERSACIONAL DE VAGAS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Criacao Conversacional de Vagas com LIA**

### O que esse fluxo entrega
Wizard conversacional guiado por IA para criar vagas de forma intuitiva, com geracao automatica de descricao, requisitos e sugestoes baseadas em historico.

### Para qual usuario
- Recrutador
- Gestor de RH
- Hiring Manager

### Resultado final esperado
Vaga completa criada com descricao profissional, requisitos estruturados e pronta para aprovacao/publicacao.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| JobCreationWizard | Wizard principal de criacao |
| LIAConversation | Chat conversacional com IA |
| JobFormSteps | Etapas do formulario |
| DescriptionEditor | Editor rico de descricao |
| RequirementsBuilder | Construtor de requisitos |
| BenefitsSelector | Seletor de beneficios |
| TemplateSelector | Seletor de templates |
| JobPreview | Preview da vaga final |
| AIAssistPanel | Painel de sugestoes IA |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/jobs | POST | Criar nova vaga |
| /api/v1/jobs/{id} | PUT | Atualizar vaga |
| /api/v1/jobs/ai/generate-description | POST | Gerar descricao com IA |
| /api/v1/jobs/ai/suggest-requirements | POST | Sugerir requisitos |
| /api/v1/jobs/ai/complete-field | POST | Autocompletar campo |
| /api/v1/jobs/templates | GET | Listar templates |
| /api/v1/jobs/similar | GET | Vagas similares para referencia |

### Dados

| Tabela | Campos |
|--------|--------|
| jobs | id, title, description, requirements, benefits, status='draft' |
| job_drafts | id, job_id, step, data_json, created_at, updated_at |
| job_ai_generations | id, job_id, field, prompt, response, accepted, created_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| CRI-F01 | Iniciar Criacao | Botao "Nova Vaga" abre wizard |
| CRI-F02 | Selecionar Template | Usar template como base |
| CRI-F03 | Informacoes Basicas | Titulo, departamento, gestor |
| CRI-F04 | Detalhes da Posicao | Modelo, local, nivel |
| CRI-F05 | Remuneracao | Faixa salarial, beneficios |
| CRI-F06 | Descricao com IA | LIA gera descricao profissional |
| CRI-F07 | Requisitos com IA | LIA sugere requisitos |
| CRI-F08 | Editar Manualmente | Ajustar textos gerados |
| CRI-F09 | Preview Final | Visualizar como candidato vera |
| CRI-F10 | Salvar Rascunho | Salvar parcialmente |
| CRI-F11 | Enviar para Aprovacao | Submeter para gestor |
| CRI-F12 | Duplicar Vaga | Criar a partir de existente |
| CRI-F13 | Importar de Template | Aplicar template completo |
| CRI-F14 | Historico de Geracoes | Ver sugestoes anteriores |
| CRI-F15 | Feedback de IA | Marcar sugestao como util/inutil |

---

## 4. Jornada do Usuario

### Cenario: Recrutador cria vaga conversando com LIA

\`\`\`
1. Recrutador clica em "Nova Vaga"
2. LIA pergunta: "Qual posicao voce precisa contratar?"
3. Recrutador digita: "Dev Backend Senior para squad de pagamentos"
4. LIA extrai: titulo="Desenvolvedor Backend Senior", dept="Tecnologia"
5. LIA sugere descricao baseada em vagas similares
6. Recrutador ajusta alguns pontos
7. LIA pergunta: "Quais sao os requisitos tecnicos?"
8. Recrutador: "Python, AWS, microservicos, 5+ anos"
9. LIA formata requisitos estruturados
10. Recrutador ve preview e envia para aprovacao
\`\`\`

---

## 5. Jornada do Sistema

\`\`\`
INICIO
  |
  v
[Usuario clica "Nova Vaga"]
  |
  v
[FRONT] Abre JobCreationWizard
  |
  v
[FRONT] Exibe etapa 1: Chat inicial com LIA
  |
  v
[Usuario descreve vaga em texto livre]
  |
  v
[FRONT] POST /api/v1/jobs/ai/generate-description
  |
  v
[BACK] Envia para Claude API
  |
  v
[IA] Analisa descricao e gera:
  - Titulo formatado
  - Departamento sugerido
  - Descricao profissional
  - Requisitos estruturados
  |
  v
[BACK] Retorna JSON com sugestoes
  |
  v
[FRONT] Popula formulario com sugestoes
  |
  v
[Usuario edita campos conforme necessario]
  |
  v
[Usuario clica "Proximo" em cada etapa]
  |
  v
[FRONT] Salva rascunho a cada etapa
  |
  v
[BACK] POST /api/v1/jobs (status=draft) ou PUT
  |
  v
[Usuario ve preview final]
  |
  v
[Usuario clica "Enviar para Aprovacao"]
  |
  v
[BACK] PUT /api/v1/jobs/{id} { status: 'pending_approval' }
  |
  v
[BACK] Notifica aprovadores via email/slack
  |
  v
[FRONT] Exibe confirmacao + proximo passo
  |
FIM
\`\`\`

---

## 6. Regras de Negocio

### Criacao

| Regra | Descricao |
|-------|-----------|
| RN-CRI-01 | Titulo obrigatorio, 5-100 caracteres |
| RN-CRI-02 | Departamento obrigatorio |
| RN-CRI-03 | Hiring Manager obrigatorio |
| RN-CRI-04 | Descricao minima de 200 caracteres |
| RN-CRI-05 | Pelo menos 3 requisitos obrigatorios |
| RN-CRI-06 | Faixa salarial opcional mas recomendada |

### IA

| Regra | Descricao |
|-------|-----------|
| RN-CRI-07 | Geracao de descricao usa contexto da empresa |
| RN-CRI-08 | Requisitos sugeridos baseados em vagas similares |
| RN-CRI-09 | Maximo 3 regeneracoes por campo por sessao |
| RN-CRI-10 | Feedback de IA salvo para melhoria continua |

### Rascunhos

| Regra | Descricao |
|-------|-----------|
| RN-CRI-11 | Rascunho salvo automaticamente a cada 30s |
| RN-CRI-12 | Rascunhos expiram em 30 dias |
| RN-CRI-13 | Maximo 10 rascunhos por usuario |

---

## 7. Requisitos Tecnicos

### Frontend

\`\`\`typescript
interface JobCreationState {
  step: number
  draft: Partial<Job>
  aiSuggestions: {
    description?: string
    requirements?: string[]
    benefits?: string[]
  }
  history: AIGenerationHistory[]
  isGenerating: boolean
  validationErrors: Record<string, string>
}

interface LIAMessage {
  id: string
  type: 'user' | 'lia' | 'system'
  content: string
  suggestions?: string[]
  actions?: Action[]
  timestamp: number
}
\`\`\`

### Backend

\`\`\`python
class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    department: str
    manager_id: UUID
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    work_model: Optional[str] = None
    location: Optional[str] = None
    seniority: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    template_id: Optional[UUID] = None

class AIGenerateDescriptionRequest(BaseModel):
    context: str
    title: Optional[str] = None
    department: Optional[str] = None
    company_context: Optional[str] = None
    similar_jobs: Optional[List[UUID]] = None
\`\`\`

### Dados

\`\`\`sql
CREATE TABLE job_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),
    user_id UUID NOT NULL REFERENCES users(id),
    step INT DEFAULT 1,
    data_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 days'
);

CREATE TABLE job_ai_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),
    user_id UUID NOT NULL REFERENCES users(id),
    field VARCHAR(50) NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    accepted BOOLEAN DEFAULT FALSE,
    feedback VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

### IA

\`\`\`python
JOB_DESCRIPTION_PROMPT = """
You are an expert technical recruiter creating a job description.

Context from user: {user_input}

Company: {company_name}
Department: {department}
Similar successful jobs: {similar_jobs}

Generate a professional job description in Portuguese (Brazil) with:
1. Brief company intro (2-3 sentences)
2. Role overview (what the person will do)
3. Key responsibilities (5-7 bullet points)
4. Growth opportunities

Tone: Professional but warm, inclusive language.
Length: 400-600 words.
"""

REQUIREMENTS_PROMPT = """
Based on this job description and title, suggest requirements.

Title: {title}
Description: {description}
Department: {department}
Seniority: {seniority}

Return JSON:
{
  "required": ["skill1", "skill2", ...],
  "nice_to_have": ["skill1", "skill2", ...],
  "experience_years": 5,
  "education": "Graduacao em Ciencia da Computacao ou areas correlatas"
}
"""
\`\`\`

---

## 8. Roadmap por Fases

### Fase 1: Formulario Basico (Sprint 1)
\`\`\`
[Formulario multi-step]
       |
       v
[Campos obrigatorios]
       |
       v
[Salvar rascunho]
       |
       v
[Criar vaga]
\`\`\`

### Fase 2: Integracao IA (Sprint 2)
\`\`\`
[Chat inicial com LIA]
       |
       v
[Geracao de descricao]
       |
       v
[Sugestao de requisitos]
       |
       v
[Feedback de sugestoes]
\`\`\`

### Fase 3: Templates (Sprint 2)
\`\`\`
[Selecionar template]
       |
       v
[Duplicar vaga existente]
       |
       v
[Importar de template]
\`\`\`

### Fase 4: Refinamentos (Sprint 3)
\`\`\`
[Editor rico de descricao]
       |
       v
[Historico de geracoes]
       |
       v
[Analytics de criacao]
\`\`\`

---

## 9. Mapeamento Tailwind para Vuetify 3

\`\`\`vue
<!-- JobCreationWizard -->
<v-stepper v-model="currentStep" alt-labels>
  <v-stepper-header>
    <v-stepper-item
      v-for="step in steps"
      :key="step.value"
      :value="step.value"
      :title="step.title"
      :complete="currentStep > step.value"
    />
  </v-stepper-header>

  <v-stepper-window>
    <v-stepper-window-item :value="1">
      <!-- Chat com LIA -->
      <v-card variant="outlined" class="pa-4">
        <v-card-title>Conte-me sobre a vaga</v-card-title>
        <v-card-text>
          <div class="chat-container">
            <div v-for="msg in messages" :key="msg.id" :class="['message', msg.type]">
              <v-avatar v-if="msg.type === 'lia'" color="primary" size="32">
                <v-icon>mdi-robot</v-icon>
              </v-avatar>
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </div>
          <v-textarea
            v-model="userInput"
            placeholder="Descreva a vaga que precisa criar..."
            variant="outlined"
            rows="3"
            :loading="isGenerating"
            @keyup.ctrl.enter="sendMessage"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="primary"
            :loading="isGenerating"
            @click="sendMessage"
          >
            Enviar
            <v-icon end>mdi-send</v-icon>
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-stepper-window-item>

    <v-stepper-window-item :value="2">
      <!-- Formulario de detalhes -->
      <v-form ref="formRef">
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="form.title"
              label="Titulo da Vaga"
              variant="outlined"
              :rules="[v => !!v || 'Titulo obrigatorio']"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="form.department"
              label="Departamento"
              :items="departments"
              variant="outlined"
            />
          </v-col>
        </v-row>
      </v-form>
    </v-stepper-window-item>
  </v-stepper-window>

  <v-stepper-actions>
    <template #prev>
      <v-btn variant="text" @click="prevStep">Voltar</v-btn>
    </template>
    <template #next>
      <v-btn color="primary" @click="nextStep">
        {{ currentStep === totalSteps ? 'Finalizar' : 'Proximo' }}
      </v-btn>
    </template>
  </v-stepper-actions>
</v-stepper>
\`\`\`

---

## 10. Pontos de Uso de IA e Fallbacks

### Pontos de IA

| Ponto | Funcao | Modelo | Latencia |
|-------|--------|--------|----------|
| Interpretacao Inicial | Entender descricao do usuario | Claude Sonnet | 1-2s |
| Geracao Descricao | Criar descricao profissional | Claude Sonnet | 2-4s |
| Sugestao Requisitos | Listar requisitos relevantes | Claude Haiku | 500ms-1s |
| Sugestao Beneficios | Listar beneficios comuns | Claude Haiku | 300-500ms |
| Autocompletar Campo | Completar texto parcial | Claude Haiku | 200-400ms |

### Riscos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Geracao lenta >5s | Media | Alto | Streaming, skeleton |
| Descricao generica | Media | Medio | Usar contexto empresa |
| Requisitos inadequados | Baixa | Alto | Revisao obrigatoria |
| Custo por vaga alto | Media | Medio | Cache, limite regeneracoes |

### Fallbacks

\`\`\`yaml
Se geracao timeout (>10s):
  1. Exibir formulario tradicional
  2. Manter campos ja preenchidos
  3. Botao "Tentar novamente"
  4. Sugerir template como alternativa

Se geracao falhar:
  1. Usar template base generico
  2. Preencher campos com placeholders editaveis
  3. Exibir: "Complete os campos manualmente"

Se API indisponivel:
  1. Modo formulario tradicional apenas
  2. Desabilitar botoes de IA
  3. Banner: "Assistente temporariamente indisponivel"
\`\`\`

---

# FLUXO 03: APROVACAO E PUBLICACAO

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Aprovacao e Publicacao Multi-Canal de Vagas**

### O que esse fluxo entrega
Workflow de aprovacao com niveis hierarquicos e publicacao automatizada em multiplos canais (LinkedIn, Website, Indeed, Glassdoor).

### Para qual usuario
- Recrutador (solicita aprovacao, publica)
- Gestor de RH (aprova)
- Diretor/VP (aprova vagas estrategicas)

### Resultado final esperado
Vaga aprovada e publicada nos canais selecionados, com rastreamento de performance por canal.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| ApprovalQueue | Fila de aprovacoes pendentes |
| ApprovalCard | Card de aprovacao com acoes |
| ApprovalHistory | Historico de aprovacoes |
| PublishingPanel | Painel de publicacao |
| ChannelSelector | Seletor de canais |
| PublishingPreview | Preview por canal |
| SchedulePublish | Agendar publicacao |
| PerformanceByChannel | Metricas por canal |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/jobs/{id}/submit-approval | POST | Enviar para aprovacao |
| /api/v1/jobs/{id}/approve | POST | Aprovar vaga |
| /api/v1/jobs/{id}/reject | POST | Rejeitar vaga |
| /api/v1/jobs/{id}/publish | POST | Publicar em canais |
| /api/v1/jobs/{id}/unpublish | POST | Despublicar |
| /api/v1/jobs/approvals/pending | GET | Listar pendentes |
| /api/v1/publishing/channels | GET | Canais disponiveis |

### Dados

| Tabela | Campos |
|--------|--------|
| job_approvals | id, job_id, approver_id, status, comments, created_at, decided_at |
| job_publications | id, job_id, channel, external_id, status, published_at, expires_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| APR-F01 | Enviar para Aprovacao | Submeter vaga |
| APR-F02 | Fila de Aprovacoes | Ver pendentes |
| APR-F03 | Aprovar Vaga | Autorizar publicacao |
| APR-F04 | Rejeitar com Feedback | Devolver com comentarios |
| APR-F05 | Aprovacao Multi-nivel | Hierarquia de aprovadores |
| APR-F06 | Notificacoes | Email/Slack para aprovadores |
| APR-F07 | Historico de Aprovacoes | Audit trail completo |
| PUB-F01 | Selecionar Canais | Escolher onde publicar |
| PUB-F02 | Preview por Canal | Ver como aparecera |
| PUB-F03 | Publicar Imediatamente | Publicar agora |
| PUB-F04 | Agendar Publicacao | Publicar em data futura |
| PUB-F05 | Despublicar | Remover de canais |
| PUB-F06 | Renovar Publicacao | Estender validade |
| PUB-F07 | Metricas por Canal | Views, applies por canal |

---

## 4. Jornada do Usuario

### Cenario: Recrutador envia vaga para aprovacao

\`\`\`
1. Recrutador finaliza criacao da vaga
2. Clica em "Enviar para Aprovacao"
3. Sistema identifica aprovador (Gestor de RH)
4. Gestor recebe notificacao por email
5. Gestor acessa fila de aprovacoes
6. Ve detalhes da vaga, descricao, salario
7. Clica em "Aprovar"
8. Vaga muda para status "Aprovada"
9. Recrutador recebe notificacao
10. Recrutador pode publicar
\`\`\`

### Cenario: Publicacao multi-canal

\`\`\`
1. Vaga aprovada aparece na lista
2. Recrutador clica em "Publicar"
3. Abre painel de canais
4. Seleciona: LinkedIn, Website, Indeed
5. Ve preview em cada formato
6. Ajusta textos especificos por canal
7. Clica em "Publicar Agora"
8. Sistema publica via APIs
9. Confirmacao com links externos
10. Metricas comecam a ser coletadas
\`\`\`

---

## 5. Jornada do Sistema

\`\`\`
INICIO
  |
  v
[Recrutador clica "Enviar para Aprovacao"]
  |
  v
[FRONT] POST /api/v1/jobs/{id}/submit-approval
  |
  v
[BACK] Identifica aprovadores por regra
  |
  v
[DADOS] INSERT INTO job_approvals (status='pending')
  |
  v
[BACK] PUT jobs SET status='pending_approval'
  |
  v
[BACK] Dispara notificacao (email/slack/push)
  |
  v
[Aprovador acessa sistema]
  |
  v
[FRONT] GET /api/v1/jobs/approvals/pending
  |
  v
[Aprovador analisa e clica "Aprovar"]
  |
  v
[FRONT] POST /api/v1/jobs/{id}/approve
  |
  v
[BACK] UPDATE job_approvals SET status='approved'
  |
  v
[BACK] UPDATE jobs SET status='approved'
  |
  v
[BACK] Notifica recrutador
  |
  v
[Recrutador clica "Publicar"]
  |
  v
[FRONT] Abre PublishingPanel
  |
  v
[Usuario seleciona canais e confirma]
  |
  v
[FRONT] POST /api/v1/jobs/{id}/publish { channels: [...] }
  |
  v
[BACK] Para cada canal:
  |
  v
[BACK] Chama API externa (LinkedIn, Indeed, etc)
  |
  v
[DADOS] INSERT INTO job_publications
  |
  v
[BACK] Retorna status de cada publicacao
  |
  v
[FRONT] Exibe confirmacao com links
  |
FIM
\`\`\`

---

## 6. Regras de Negocio

### Aprovacao

| Regra | Descricao |
|-------|-----------|
| RN-APR-01 | Vaga precisa de aprovacao para publicar |
| RN-APR-02 | Aprovador padrao e Gestor de RH |
| RN-APR-03 | Vagas com salario >R$30k precisam de Diretor |
| RN-APR-04 | Rejeicao requer comentario |
| RN-APR-05 | Aprovacao expira em 7 dias |
| RN-APR-06 | Recrutador pode cancelar aprovacao pendente |

### Publicacao

| Regra | Descricao |
|-------|-----------|
| RN-PUB-01 | Publicacao requer vaga aprovada |
| RN-PUB-02 | LinkedIn exige empresa verificada |
| RN-PUB-03 | Publicacao padrao vale 30 dias |
| RN-PUB-04 | Limite de 10 publicacoes simultaneas por canal free |
| RN-PUB-05 | Despublicar remove de todos os canais |
| RN-PUB-06 | Editar vaga publicada requer nova aprovacao |

---

## 7. Requisitos Tecnicos

### Frontend

\`\`\`typescript
interface ApprovalState {
  pendingApprovals: ApprovalItem[]
  myRequests: ApprovalItem[]
  isLoading: boolean
}

interface PublishingState {
  selectedChannels: string[]
  previews: Record<string, string>
  isPublishing: boolean
  publishedChannels: PublicationStatus[]
}

interface PublicationStatus {
  channel: string
  status: 'published' | 'failed' | 'pending'
  externalUrl?: string
  externalId?: string
  publishedAt?: string
  error?: string
}
\`\`\`

### Backend

\`\`\`python
class ApprovalRequest(BaseModel):
    comments: Optional[str] = None

class PublishRequest(BaseModel):
    channels: List[str]
    schedule_at: Optional[datetime] = None
    custom_texts: Optional[Dict[str, str]] = None

class PublishingService:
    async def publish_to_channel(self, job: Job, channel: str) -> PublicationResult:
        if channel == "linkedin":
            return await self.linkedin_client.post_job(job)
        elif channel == "indeed":
            return await self.indeed_client.post_job(job)
        elif channel == "website":
            return await self.website_service.publish(job)
\`\`\`

### Dados

\`\`\`sql
CREATE TABLE job_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    approver_id UUID NOT NULL REFERENCES users(id),
    requester_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    decided_at TIMESTAMP,
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
);

CREATE TABLE job_publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    channel VARCHAR(50) NOT NULL,
    external_id VARCHAR(200),
    external_url TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    published_at TIMESTAMP,
    expires_at TIMESTAMP,
    views_count INT DEFAULT 0,
    applies_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

---

## 8. Roadmap por Fases

### Fase 1: Aprovacao Simples (Sprint 2)
\`\`\`
[Enviar para aprovacao]
       |
       v
[Fila de pendentes]
       |
       v
[Aprovar/Rejeitar]
\`\`\`

### Fase 2: Publicacao Website (Sprint 2)
\`\`\`
[Publicar no website interno]
       |
       v
[Despublicar]
       |
       v
[Metricas basicas]
\`\`\`

### Fase 3: Multi-Canal (Sprint 3)
\`\`\`
[Integracao LinkedIn]
       |
       v
[Integracao Indeed]
       |
       v
[Preview por canal]
\`\`\`

### Fase 4: Avancado (Sprint 4)
\`\`\`
[Agendamento]
       |
       v
[Aprovacao multi-nivel]
       |
       v
[Analytics por canal]
\`\`\`

---

## 9. Mapeamento Tailwind para Vuetify 3

\`\`\`vue
<!-- ApprovalQueue -->
<v-card>
  <v-card-title>Aprovacoes Pendentes</v-card-title>
  <v-list>
    <v-list-item
      v-for="approval in pendingApprovals"
      :key="approval.id"
      :title="approval.job.title"
      :subtitle="formatDate(approval.created_at)"
    >
      <template #prepend>
        <v-avatar color="primary" size="40">
          <v-icon>mdi-briefcase</v-icon>
        </v-avatar>
      </template>
      <template #append>
        <v-btn
          color="success"
          variant="tonal"
          size="small"
          class="mr-2"
          @click="approve(approval.id)"
        >
          Aprovar
        </v-btn>
        <v-btn
          color="error"
          variant="tonal"
          size="small"
          @click="openRejectDialog(approval)"
        >
          Rejeitar
        </v-btn>
      </template>
    </v-list-item>
  </v-list>
</v-card>

<!-- PublishingPanel -->
<v-dialog v-model="showPublishDialog" max-width="800">
  <v-card>
    <v-card-title>Publicar Vaga</v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="12" md="4">
          <v-card
            v-for="channel in channels"
            :key="channel.id"
            variant="outlined"
            :class="{ 'border-primary': isSelected(channel.id) }"
            class="mb-2 cursor-pointer"
            @click="toggleChannel(channel.id)"
          >
            <v-card-text class="d-flex align-center">
              <v-checkbox
                :model-value="isSelected(channel.id)"
                hide-details
                density="compact"
              />
              <v-avatar size="32" class="mx-2">
                <v-img :src="channel.logo" />
              </v-avatar>
              <span>{{ channel.name }}</span>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="8">
          <v-tabs v-model="previewTab">
            <v-tab v-for="ch in selectedChannels" :key="ch" :value="ch">
              {{ ch }}
            </v-tab>
          </v-tabs>
          <v-tabs-window v-model="previewTab">
            <v-tabs-window-item v-for="ch in selectedChannels" :key="ch" :value="ch">
              <div class="preview-container pa-4" v-html="previews[ch]" />
            </v-tabs-window-item>
          </v-tabs-window>
        </v-col>
      </v-row>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" @click="showPublishDialog = false">Cancelar</v-btn>
      <v-btn color="primary" :loading="isPublishing" @click="publish">
        Publicar
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
\`\`\`

---

## 10. Pontos de Uso de IA e Fallbacks

### Pontos de IA

| Ponto | Funcao | Modelo | Latencia |
|-------|--------|--------|----------|
| Otimizacao por Canal | Adaptar texto para formato do canal | Claude Haiku | 500ms-1s |
| SEO de Vaga | Sugerir keywords para melhor ranking | Claude Haiku | 300-500ms |

### Fallbacks

\`\`\`yaml
Se LinkedIn API falhar:
  1. Salvar como pendente
  2. Retry automatico em 5 minutos
  3. Notificar usuario se persistir

Se Indeed indisponivel:
  1. Pular canal
  2. Publicar nos demais
  3. Notificar para tentativa manual
\`\`\`

---

# FLUXO 04: KANBAN DE CANDIDATOS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Kanban de Gestao de Pipeline de Candidatos**

### O que esse fluxo entrega
Interface visual Kanban para gerenciar candidatos em cada etapa do processo seletivo, com drag-and-drop, cards ricos e acoes rapidas.

### Para qual usuario
- Recrutador
- Tech Recruiter
- Hiring Manager

### Resultado final esperado
Visao clara do pipeline de candidatos por etapa, com capacidade de mover candidatos, agendar entrevistas e tomar decisoes rapidamente.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| JobKanbanPage | Pagina do Kanban da vaga |
| KanbanBoard | Board com colunas de etapas |
| KanbanColumn | Coluna de uma etapa |
| CandidateCard | Card do candidato |
| CandidatePreview | Preview lateral detalhado |
| StageHeader | Header da coluna com stats |
| QuickActions | Acoes rapidas no card |
| BulkActionsBar | Barra de acoes em lote |
| DragDropProvider | Provider de drag-and-drop |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/jobs/{id}/pipeline | GET | Candidatos por etapa |
| /api/v1/jobs/{id}/candidates | GET | Todos os candidatos |
| /api/v1/jobs/{id}/candidates/{cid}/move | POST | Mover de etapa |
| /api/v1/jobs/{id}/candidates/{cid}/reject | POST | Reprovar candidato |
| /api/v1/jobs/{id}/candidates/{cid}/approve | POST | Aprovar candidato |
| /api/v1/jobs/{id}/stages | GET | Etapas configuradas |
| /api/v1/jobs/{id}/stages | PUT | Reordenar etapas |

### Dados

| Tabela | Campos |
|--------|--------|
| job_applications | id, job_id, candidate_id, stage_id, status, applied_at, moved_at |
| job_stages | id, job_id, name, order, color, is_final |
| stage_transitions | id, application_id, from_stage_id, to_stage_id, moved_by, moved_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| KAN-F01 | Visualizar Kanban | Ver pipeline visual |
| KAN-F02 | Drag and Drop | Mover candidatos entre etapas |
| KAN-F03 | Card de Candidato | Exibir info resumida |
| KAN-F04 | Preview Lateral | Detalhes completos |
| KAN-F05 | Score LIA | Exibir score de triagem |
| KAN-F06 | Alerts/Warnings | Indicadores de atencao |
| KAN-F07 | Quick Actions | Acoes rapidas no hover |
| KAN-F08 | Filtrar Pipeline | Por source, score, etc |
| KAN-F09 | Ordenar Colunas | Por score, data, nome |
| KAN-F10 | Colapsar Colunas | Minimizar colunas |
| KAN-F11 | Bulk Move | Mover varios de uma vez |
| KAN-F12 | Bulk Reject | Reprovar em lote |
| KAN-F13 | Configurar Etapas | Adicionar/remover/reordenar |
| KAN-F14 | Historico de Movimentacao | Ver transicoes |
| KAN-F15 | Tempo por Etapa | Metricas de tempo |

---

## 4. Jornada do Usuario

### Cenario: Recrutador gerencia pipeline

\`\`\`
1. Recrutador acessa vaga no Kanban
2. Ve 4 colunas: Triagem (15), Entrevista (8), Final (3), Aprovados (1)
3. Hover em card mostra score LIA, skills, foto
4. Clica em card para abrir preview lateral
5. Ve Big Five, experiencia, notas
6. Arrasta candidato de "Entrevista" para "Final"
7. Sistema registra transicao
8. Notificacao enviada ao candidato
9. Recrutador ve alerta em card: "Aguardando feedback >3 dias"
10. Clica em acao rapida "Enviar lembrete"
\`\`\`

### Cenario: Reprovacao em lote

\`\`\`
1. Recrutador filtra por score < 70
2. Seleciona 5 candidatos
3. Clica em "Reprovar Selecionados"
4. Escolhe motivo e template de feedback
5. Confirma acao
6. Sistema move para "Reprovados"
7. Emails de feedback enviados automaticamente
\`\`\`

---

## 5. Jornada do Sistema

\`\`\`
INICIO
  |
  v
[Usuario acessa /jobs/{id}/kanban]
  |
  v
[FRONT] GET /api/v1/jobs/{id}/pipeline
  |
  v
[BACK] Query candidatos agrupados por stage
  |
  v
[DADOS] SELECT * FROM job_applications WHERE job_id = X GROUP BY stage_id
  |
  v
[BACK] Enriquece com dados do candidato e score
  |
  v
[FRONT] Renderiza KanbanBoard com colunas
  |
  v
[Usuario arrasta card]
  |
  v
[FRONT] Evento onDragEnd
  |
  v
[FRONT] POST /api/v1/jobs/{id}/candidates/{cid}/move
  |
  v
[BACK] Valida transicao permitida
  |
  v
[DADOS] UPDATE job_applications SET stage_id = Y
  |
  v
[DADOS] INSERT INTO stage_transitions
  |
  v
[BACK] Dispara webhook/notificacao
  |
  v
[FRONT] Atualiza UI otimisticamente
  |
FIM
\`\`\`

---

## 6. Regras de Negocio

### Pipeline

| Regra | Descricao |
|-------|-----------|
| RN-KAN-01 | Etapas padrao: Triagem, Entrevista, Final, Aprovado, Reprovado |
| RN-KAN-02 | Candidato so pode estar em uma etapa |
| RN-KAN-03 | Mover para "Aprovado" dispara fluxo de contratacao |
| RN-KAN-04 | Mover para "Reprovado" dispara envio de feedback |
| RN-KAN-05 | Transicoes reversas permitidas |
| RN-KAN-06 | Limite de 500 candidatos por vaga |

### Permissoes

| Regra | Descricao |
|-------|-----------|
| RN-KAN-07 | Recrutador pode mover candidatos |
| RN-KAN-08 | Gestor pode mover e aprovar final |
| RN-KAN-09 | Visualizador so pode ver |

---

## 7. Requisitos Tecnicos

### Frontend

\`\`\`typescript
interface KanbanState {
  stages: Stage[]
  candidatesByStage: Record<string, Candidate[]>
  selectedCandidates: Set<string>
  draggedCandidate: Candidate | null
  isLoading: boolean
}

interface Stage {
  id: string
  name: string
  order: number
  color: string
  candidatesCount: number
  isFinal: boolean
}

interface Candidate {
  id: string
  name: string
  role: string
  currentCompany: string
  avatar: string
  score: number
  fitScore: number
  source: string
  appliedAt: string
  daysInStage: number
  needsAction: boolean
  alerts: Alert[]
}
\`\`\`

### Backend

\`\`\`python
class PipelineResponse(BaseModel):
    stages: List[StageWithCandidates]
    total_candidates: int
    metrics: PipelineMetrics

class MoveRequest(BaseModel):
    to_stage_id: UUID
    notes: Optional[str] = None
    notify_candidate: bool = True
\`\`\`

### Dados

\`\`\`sql
CREATE TABLE job_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    name VARCHAR(50) NOT NULL,
    order_num INT NOT NULL,
    color VARCHAR(20) DEFAULT '#60BED1',
    is_final BOOLEAN DEFAULT FALSE,
    is_rejection BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE stage_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES job_applications(id),
    from_stage_id UUID REFERENCES job_stages(id),
    to_stage_id UUID NOT NULL REFERENCES job_stages(id),
    moved_by UUID NOT NULL REFERENCES users(id),
    notes TEXT,
    moved_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

---

## 8. Roadmap por Fases

### Fase 1: Kanban Basico (Sprint 2)
\`\`\`
[Visualizar colunas]
       |
       v
[Cards de candidatos]
       |
       v
[Drag and drop]
\`\`\`

### Fase 2: Interacoes (Sprint 2-3)
\`\`\`
[Preview lateral]
       |
       v
[Quick actions]
       |
       v
[Filtros e ordenacao]
\`\`\`

### Fase 3: Bulk Actions (Sprint 3)
\`\`\`
[Multi-select]
       |
       v
[Move em lote]
       |
       v
[Rejeitar em lote]
\`\`\`

### Fase 4: Configuracao (Sprint 4)
\`\`\`
[Customizar etapas]
       |
       v
[Cores e ordem]
       |
       v
[Metricas por etapa]
\`\`\`

---

## 9. Mapeamento Tailwind para Vuetify 3

\`\`\`vue
<!-- KanbanBoard -->
<v-container fluid class="kanban-container">
  <div class="kanban-board d-flex gap-4 overflow-x-auto pa-4">
    <v-card
      v-for="stage in stages"
      :key="stage.id"
      class="kanban-column"
      :style="{ minWidth: '300px', maxWidth: '350px' }"
      variant="outlined"
    >
      <v-card-title class="d-flex align-center justify-space-between pa-3">
        <div class="d-flex align-center gap-2">
          <div
            class="stage-dot"
            :style="{ backgroundColor: stage.color, width: '12px', height: '12px', borderRadius: '50%' }"
          />
          <span class="text-subtitle-1 font-weight-medium">{{ stage.name }}</span>
          <v-chip size="small" variant="tonal">{{ stage.candidatesCount }}</v-chip>
        </div>
        <v-menu>
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-dots-vertical" variant="text" size="small" />
          </template>
          <v-list density="compact">
            <v-list-item @click="sortColumn(stage.id, 'score')">
              Ordenar por Score
            </v-list-item>
            <v-list-item @click="collapseColumn(stage.id)">
              Minimizar
            </v-list-item>
          </v-list>
        </v-menu>
      </v-card-title>

      <v-card-text class="pa-2" style="max-height: 70vh; overflow-y: auto;">
        <draggable
          v-model="candidatesByStage[stage.id]"
          group="candidates"
          item-key="id"
          @end="onDragEnd"
        >
          <template #item="{ element }">
            <v-card
              class="candidate-card mb-2"
              variant="outlined"
              :class="{ 'border-warning': element.needsAction }"
              @click="openPreview(element)"
            >
              <v-card-text class="pa-3">
                <div class="d-flex align-center gap-2 mb-2">
                  <v-avatar size="40">
                    <v-img :src="element.avatar" />
                  </v-avatar>
                  <div class="flex-grow-1">
                    <div class="text-subtitle-2 font-weight-medium">{{ element.name }}</div>
                    <div class="text-caption text-grey">{{ element.role }}</div>
                  </div>
                  <v-chip
                    size="x-small"
                    :color="getScoreColor(element.score)"
                    variant="tonal"
                  >
                    {{ element.score }}
                  </v-chip>
                </div>
                <div class="d-flex gap-1 flex-wrap">
                  <v-chip
                    v-for="alert in element.alerts"
                    :key="alert.type"
                    size="x-small"
                    color="warning"
                    variant="flat"
                  >
                    {{ alert.message }}
                  </v-chip>
                </div>
              </v-card-text>
            </v-card>
          </template>
        </draggable>
      </v-card-text>
    </v-card>
  </div>
</v-container>
\`\`\`

---

## 10. Pontos de Uso de IA e Fallbacks

### Pontos de IA

| Ponto | Funcao | Modelo | Latencia |
|-------|--------|--------|----------|
| Score LIA | Calculo de fit do candidato | Claude Sonnet | Pre-calculado |
| Alertas Inteligentes | Detectar candidatos parados | Rules + Haiku | 200ms |
| Sugestao de Acao | Recomendar proxima acao | Claude Haiku | 300-500ms |

### Fallbacks

\`\`\`yaml
Se drag-drop falhar:
  1. Retry automatico
  2. Se persistir, usar botao "Mover para"
  3. Fallback para modal de selecao de etapa

Se preview nao carregar:
  1. Exibir dados basicos do cache
  2. Botao "Recarregar"
\`\`\`

---

# FLUXO 05: TRIAGEM E AVALIACAO

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Triagem Automatizada e Avaliacao com LIA**

### O que esse fluxo entrega
Sistema de triagem automatizada de candidatos usando IA, com calculo de score, envio de testes e integracao com WSI (Work Style Index).

### Para qual usuario
- Recrutador
- Tech Recruiter

### Resultado final esperado
Candidatos triados automaticamente com scores, resultados de testes tecnicos e perfil comportamental (Big Five).

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| ScreeningDashboard | Dashboard de triagem |
| CandidateScoreCard | Card com scores |
| TriagemProgress | Progresso da triagem |
| TestResultsPanel | Resultados de testes |
| BigFiveChart | Grafico Big Five |
| WSIResults | Resultados WSI |
| ScreeningSettings | Configuracoes de triagem |
| AutoRejectRules | Regras de rejeicao automatica |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/screening/start | POST | Iniciar triagem |
| /api/v1/screening/{id}/status | GET | Status da triagem |
| /api/v1/screening/{id}/score | GET | Score calculado |
| /api/v1/screening/tests/{id}/send | POST | Enviar teste |
| /api/v1/screening/tests/{id}/results | GET | Resultados do teste |
| /api/v1/wsi/assess | POST | Avaliar WSI |

### Dados

| Tabela | Campos |
|--------|--------|
| screening_sessions | id, application_id, status, started_at, completed_at |
| screening_scores | id, session_id, score_type, value, details_json |
| candidate_tests | id, candidate_id, test_type, status, score, completed_at |
| wsi_assessments | id, candidate_id, big_five_json, work_style_json |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| TRI-F01 | Iniciar Triagem | Comecar processo automatizado |
| TRI-F02 | Analisar CV | IA analisa curriculo |
| TRI-F03 | Calcular Fit Score | Score de match com vaga |
| TRI-F04 | Calcular Skills Match | Match de competencias |
| TRI-F05 | Enviar Teste Tecnico | Teste online |
| TRI-F06 | Enviar WSI | Avaliacao comportamental |
| TRI-F07 | Aguardar Respostas | Tracking de pendencias |
| TRI-F08 | Processar Resultados | Consolidar scores |
| TRI-F09 | Gerar Score Final | Score LIA consolidado |
| TRI-F10 | Auto-aprovar | Regra automatica de aprovacao |
| TRI-F11 | Auto-reprovar | Regra automatica de rejeicao |
| TRI-F12 | Big Five Chart | Exibir perfil comportamental |
| TRI-F13 | Comparar com Vaga | Match de perfil esperado |
| TRI-F14 | Ranking | Ordenar por score |
| TRI-F15 | Notificar Recrutador | Alertar sobre resultados |

---

## 4. Jornada do Usuario

### Cenario: Triagem automatica de novos candidatos

\`\`\`
1. Novo candidato se aplica para vaga
2. Sistema inicia triagem automatica
3. LIA analisa CV e extrai entidades
4. Sistema calcula fit score inicial (70%)
5. Sistema envia convite para teste tecnico
6. Candidato completa teste (score 85%)
7. Sistema envia WSI para Big Five
8. Candidato completa (Conscientiousness alto)
9. Score final calculado: 82%
10. Recrutador recebe notificacao
11. Candidato aparece em "Triados - Aprovados"
\`\`\`

### Cenario: Rejeicao automatica

\`\`\`
1. Candidato se aplica
2. CV analisado: 2 anos experiencia
3. Vaga exige: 5+ anos (requisito eliminatorio)
4. Score fit inicial: 45%
5. Regra de auto-reject: score < 50%
6. Candidato movido para "Triagem - Reprovado"
7. Email de feedback enviado automaticamente
8. Recrutador ve no dashboard: "1 auto-rejeitado"
\`\`\`

---

## 5. Jornada do Sistema

\`\`\`
INICIO
  |
  v
[Novo candidato se aplica]
  |
  v
[BACK] Trigger: novo job_application
  |
  v
[BACK] Cria screening_session
  |
  v
[BACK] Envia CV para Claude API
  |
  v
[IA] Extrai: skills, experiencia, educacao
  |
  v
[BACK] Compara com job requirements
  |
  v
[IA] Calcula fit score (0-100)
  |
  v
[DADOS] INSERT INTO screening_scores
  |
  v
[BACK] Verifica regras auto-reject
  |
  v
Se score >= threshold:
  |
  v
[BACK] Envia convite teste tecnico (email)
  |
  v
[Candidato completa teste]
  |
  v
[BACK] Recebe webhook com resultado
  |
  v
[DADOS] UPDATE candidate_tests
  |
  v
[BACK] Envia convite WSI (email)
  |
  v
[Candidato completa WSI]
  |
  v
[BACK] Recebe resultado Big Five
  |
  v
[DADOS] INSERT INTO wsi_assessments
  |
  v
[BACK] Calcula score final consolidado
  |
  v
[DADOS] UPDATE screening_scores (final)
  |
  v
[BACK] Atualiza status: triagem_completa
  |
  v
[BACK] Notifica recrutador
  |
FIM
\`\`\`

---

## 6. Regras de Negocio

### Triagem

| Regra | Descricao |
|-------|-----------|
| RN-TRI-01 | Triagem inicia automaticamente apos aplicacao |
| RN-TRI-02 | Fit score calculado em ate 60 segundos |
| RN-TRI-03 | Score final = 40% CV + 30% Teste + 30% WSI |
| RN-TRI-04 | Auto-reject se score < 50% |
| RN-TRI-05 | Auto-approve se score >= 85% |
| RN-TRI-06 | Timeout de 7 dias para completar testes |

### Testes

| Regra | Descricao |
|-------|-----------|
| RN-TRI-07 | Teste tecnico opcional (configuravel por vaga) |
| RN-TRI-08 | WSI recomendado para vagas senior |
| RN-TRI-09 | Re-teste permitido apos 30 dias |

---

## 7. Requisitos Tecnicos

### Frontend

\`\`\`typescript
interface ScreeningState {
  sessions: ScreeningSession[]
  currentSession: ScreeningSession | null
  scores: Record<string, Score>
  bigFiveData: BigFiveAssessment | null
}

interface ScreeningSession {
  id: string
  candidateId: string
  status: 'pending' | 'cv_analysis' | 'testing' | 'completed'
  scores: {
    cv: number | null
    technical: number | null
    wsi: number | null
    final: number | null
  }
  startedAt: string
  completedAt: string | null
}
\`\`\`

### Backend

\`\`\`python
class ScreeningService:
    async def start_screening(self, application_id: UUID) -> ScreeningSession:
        session = await self.create_session(application_id)
        await self.analyze_cv(session)
        await self.calculate_fit_score(session)
        await self.check_auto_rules(session)
        return session

    async def calculate_final_score(self, session_id: UUID) -> float:
        scores = await self.get_all_scores(session_id)
        weights = self.get_weights()
        return sum(s * w for s, w in zip(scores, weights))
\`\`\`

### IA

\`\`\`python
CV_ANALYSIS_PROMPT = """
Analyze this candidate CV for the following job.

Job Requirements:
{job_requirements}

Candidate CV:
{cv_text}

Extract and evaluate:
1. Years of experience (number)
2. Relevant skills (list with proficiency 1-5)
3. Education match (0-100)
4. Career progression quality (0-100)
5. Red flags (list)
6. Highlights (list)

Return JSON with fit_score (0-100) and detailed breakdown.
"""
\`\`\`

---

## 8. Roadmap por Fases

### Fase 1: Analise CV (Sprint 2)
### Fase 2: Testes (Sprint 3)
### Fase 3: Automacao (Sprint 3-4)

---

## 9. Mapeamento Tailwind para Vuetify 3

\`\`\`vue
<!-- ScreeningScoreCard -->
<v-card>
  <v-card-title class="d-flex align-center gap-2">
    <v-icon color="primary">mdi-brain</v-icon>
    Score LIA
  </v-card-title>
  <v-card-text>
    <div class="text-center mb-4">
      <v-progress-circular
        :model-value="scores.final"
        :size="120"
        :width="12"
        :color="getScoreColor(scores.final)"
      >
        <span class="text-h4">{{ scores.final }}</span>
      </v-progress-circular>
    </div>
    
    <v-list density="compact">
      <v-list-item>
        <template #prepend>
          <v-icon size="small">mdi-file-document</v-icon>
        </template>
        <v-list-item-title>Analise CV</v-list-item-title>
        <template #append>
          <v-chip size="small" :color="getScoreColor(scores.cv)">
            {{ scores.cv }}%
          </v-chip>
        </template>
      </v-list-item>
      <v-list-item>
        <template #prepend>
          <v-icon size="small">mdi-code-tags</v-icon>
        </template>
        <v-list-item-title>Teste Tecnico</v-list-item-title>
        <template #append>
          <v-chip size="small" :color="getScoreColor(scores.technical)">
            {{ scores.technical }}%
          </v-chip>
        </template>
      </v-list-item>
      <v-list-item>
        <template #prepend>
          <v-icon size="small">mdi-account-heart</v-icon>
        </template>
        <v-list-item-title>WSI / Big Five</v-list-item-title>
        <template #append>
          <v-chip size="small" :color="getScoreColor(scores.wsi)">
            {{ scores.wsi }}%
          </v-chip>
        </template>
      </v-list-item>
    </v-list>
  </v-card-text>
</v-card>
\`\`\`

---

## 10. Pontos de Uso de IA e Fallbacks

### Pontos de IA

| Ponto | Funcao | Modelo | Latencia |
|-------|--------|--------|----------|
| Parsing CV | Extrair informacoes do CV | Claude Sonnet | 2-5s |
| Fit Score | Calcular match com vaga | Claude Sonnet | 1-3s |
| Skills Match | Mapear competencias | Claude Haiku | 500ms-1s |

### Fallbacks

\`\`\`yaml
Se parsing CV falhar:
  1. Usar parsing regex basico
  2. Marcar para revisao manual
  3. Score parcial apenas

Se Claude indisponivel:
  1. Enqueue para processamento posterior
  2. Marcar candidato como "pendente analise"
  3. Notificar recrutador
\`\`\`

---

# FLUXO 06: COMUNICACAO COM CANDIDATOS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Comunicacao Multi-Canal com Candidatos**

### O que esse fluxo entrega
Sistema de comunicacao com candidatos via email e WhatsApp, com templates editaveis e envio em lote.

### Para qual usuario
- Recrutador
- Tech Recruiter

### Resultado final esperado
Comunicacao eficiente com candidatos usando templates profissionais e rastreamento de entregas.

---

## 2-10. (Detalhes similares aos fluxos anteriores)

---

# FLUXO 07: AGENDAMENTO DE ENTREVISTAS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Agendamento Inteligente de Entrevistas**

### O que esse fluxo entrega
Sistema de agendamento de entrevistas com integracao de calendario, Teams/Zoom e slots disponiveis automaticos.

### Para qual usuario
- Recrutador
- Entrevistador

### Resultado final esperado
Entrevistas agendadas sem conflitos, com convites enviados e lembretes automaticos.

---

## 2-10. (Detalhes similares aos fluxos anteriores)

---

# FLUXO 08: RELATORIOS E ANALYTICS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Relatorios e Analytics de Vagas**

### O que esse fluxo entrega
Dashboards e relatorios completos sobre performance de vagas, funil de conversao, metricas de recrutamento e NPS.

### Para qual usuario
- Recrutador
- Gestor de RH
- Diretoria

### Resultado final esperado
Visibilidade completa sobre metricas de recrutamento com insights acionaveis.

---

## 2-10. (Detalhes similares aos fluxos anteriores)

---

# FLUXO 09: TEMPLATES DE VAGAS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Gestao de Templates de Vagas**

### O que esse fluxo entrega
Sistema de CRUD de templates de vagas reutilizaveis, com geracao assistida por IA.

### Para qual usuario
- Recrutador
- Gestor de RH

### Resultado final esperado
Biblioteca de templates prontos para acelerar criacao de vagas.

---

## 2-10. (Detalhes similares aos fluxos anteriores)

---

# FLUXO 10: ASSISTENTE LIA DE VAGAS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Assistente LIA Copilot para Recrutadores**

### O que esse fluxo entrega
Assistente de IA conversacional embarcado na interface de vagas para responder perguntas, gerar insights e executar acoes.

### Para qual usuario
- Recrutador
- Tech Recruiter
- Gestor de RH

### Resultado final esperado
Produtividade aumentada com respostas instantaneas e automacao de tarefas repetitivas.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| LIAPrompt | Campo de input principal |
| LIAChatPanel | Painel de chat expandido |
| LIAMessage | Mensagem no chat |
| LIASuggestions | Sugestoes de comandos |
| LIAActionCards | Acoes executaveis |
| LIAInsightsPanel | Insights gerados |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/lia/chat | POST | Enviar mensagem |
| /api/v1/lia/actions | POST | Executar acao |
| /api/v1/lia/insights | GET | Obter insights |
| /api/v1/lia/suggestions | GET | Sugestoes contextuais |

### Dados

| Tabela | Campos |
|--------|--------|
| lia_conversations | id, user_id, context, messages_json, created_at |
| lia_actions_log | id, user_id, action_type, parameters_json, result, created_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| LIA-F01 | Chat Natural | Conversar em linguagem natural |
| LIA-F02 | Responder Perguntas | Sobre vagas e candidatos |
| LIA-F03 | Gerar Insights | Analises automaticas |
| LIA-F04 | Executar Acoes | Filtrar, mover, enviar |
| LIA-F05 | Sugestoes Contextuais | Comandos sugeridos |
| LIA-F06 | Resumir Vagas | Overview rapido |
| LIA-F07 | Comparar Vagas | Side-by-side |
| LIA-F08 | Alertas Proativos | "Voce tem X urgentes" |
| LIA-F09 | Historico Chat | Ver conversas anteriores |
| LIA-F10 | Aprender Preferencias | Personalizar respostas |

---

## 4-10. (Detalhes completos como nos primeiros fluxos)

---

# APENDICE: RESUMO DE INTEGRACAO COM IA

## Mapa de Uso de IA por Fluxo

| Fluxo | Usa IA | Modelo Principal | Funcao |
|-------|--------|------------------|--------|
| 01 - Listagem | Sim | Claude Haiku | Busca semantica |
| 02 - Criacao | Sim | Claude Sonnet | Geracao de descricao |
| 03 - Aprovacao | Parcial | Claude Haiku | Otimizacao por canal |
| 04 - Kanban | Parcial | Pre-calculado | Score LIA |
| 05 - Triagem | Sim | Claude Sonnet | Analise CV, Fit Score |
| 06 - Comunicacao | Parcial | Claude Haiku | Sugestao de tom |
| 07 - Agendamento | Nao | - | - |
| 08 - Relatorios | Parcial | Claude Haiku | Insights automaticos |
| 09 - Templates | Sim | Claude Sonnet | Geracao de templates |
| 10 - LIA Chat | Sim | Claude Sonnet | Chat conversacional |

## Estimativa de Custos de IA

| Operacao | Modelo | Tokens (avg) | Custo estimado |
|----------|--------|--------------|----------------|
| Busca semantica | Haiku | 500 | $0.0005 |
| Geracao descricao | Sonnet | 2000 | $0.006 |
| Analise CV | Sonnet | 3000 | $0.009 |
| Chat LIA | Sonnet | 1500 | $0.0045 |
| Template | Sonnet | 2500 | $0.0075 |

---

*Documento gerado para o modulo Gestao de Vagas - Plataforma LIA*
*Versao 1.0 - Dezembro 2024*
