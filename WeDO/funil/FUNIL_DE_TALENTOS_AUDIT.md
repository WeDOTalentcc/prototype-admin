# Auditoria Completa: Funil de Talentos
**Data:** 10 de Dezembro de 2025  
**Versão:** 1.0  
**Feature:** Funil de Talentos (Talent Pipeline)  
**Rota:** `/funil`

---

## 📋 RESUMO EXECUTIVO

### O que é a Feature
O **Funil de Talentos** é o módulo central de busca, visualização e gestão de candidatos da plataforma LIA. Permite busca híbrida (base local + Pearch AI), aplicação de filtros avançados, preview de candidatos, ações em lote, integração com sistema de opiniões (Pareceres LIA), e WSI (Work Sample Interview).

### Principais Riscos Identificados
1. **Monolito de 12.000 linhas** - `candidates-page.tsx` concentra UI, lógica de negócio e orquestração
2. **Estado fragmentado** - Mix de localStorage + API sem sincronização garantida
3. **Contratos de API divergentes** - FastAPI/Pydantic não mapeados para Rails/ActiveRecord
4. **Integração AI ad-hoc** - Claude/LangGraph embutidos em componentes React
5. **Multi-tenancy frágil** - `company_id` não consistente em todos os endpoints

### Esforço Estimado
| Cenário | Tempo |
|---------|-------|
| Ideal | 12-16 semanas |
| Realista | 20-24 semanas |
| Pessimista | 28-32 semanas |

### Recomendação Estratégica
Implementar refatoração progressiva em 4 fases: (1) Modularização do monolito React, (2) Consolidação de estado, (3) Padronização de contratos API, (4) Migração para Rails + Vue.

---

## ✅ CHECKLIST DE AUDITORIA - 32 ITENS

---

### 1. Padrão de Design (UI / UX / Design System)

#### a) Diagnóstico do Estado Atual
- **Cores**: Palette monochromática (gray-50 a gray-900) + accent #60BED1
- **Fontes**: Source Serif 4 para títulos, Open Sans para body
- **Grid**: Tailwind CSS responsivo com breakpoints padrão
- **Componentes**: shadcn/ui + Radix UI primitives
- **Estados Visuais**: hover/focus/disabled implementados via Tailwind
- **Responsividade**: Mobile-first, mas algumas tabelas overflow em mobile

#### b) Riscos e Impactos
- Inconsistência entre font-weight em diferentes seções (títulos bold, alguns dados bold quando deviam ser normal)
- Cards com padrões variados (alguns com shadow-sm, outros sem)
- Falta de Design Tokens formais - tudo hardcoded em classes Tailwind

#### c) Recomendações Concretas
1. Criar arquivo `design-tokens.ts` com constantes de cores, espaçamentos, shadows
2. Padronizar tipografia: `font-semibold` apenas para headers e primary identifiers
3. Criar variantes de Card no Storybook: CardCompact, CardExpanded, CardInteractive

#### d) Mapeamento Figma → Tailwind → Vuetify
| Figma Token | Tailwind Class | Vuetify Equivalent |
|-------------|----------------|-------------------|
| Primary Color | `bg-[#60BED1]` | `color="primary"` |
| Card Border | `border-gray-100` | `outlined` prop |
| Shadow Default | `shadow-sm` | `elevation="1"` |
| Title Font | `text-[13px] font-semibold` | `v-card-title` |
| Body Font | `text-[11px] text-gray-600` | `v-card-text` |

---

### 2. Infraestrutura

#### a) Diagnóstico do Estado Atual
```
Frontend: Next.js 14 (App Router) → Replit
Backend: FastAPI + LangGraph → Replit (porta 8000)
Proxy: /api/backend-proxy/* → FastAPI
Database: PostgreSQL (Neon-backed via Replit)
Cache: Não implementado (risco de performance)
Filas: RabbitMQ configurado mas subutilizado
Storage: Não há storage de arquivos persistente
IA: Claude API (Anthropic) + Google Gemini para transcrição
```

#### b) Riscos e Impactos
- Sem cache Redis para buscas frequentes
- Pearch API calls não são idempotentes nem retryable
- Sem circuit breaker para APIs externas
- Ausência de rate limiting no frontend

#### c) Recomendações Concretas
1. Implementar Redis para cache de buscas (TTL 5min para local, 1h para Pearch)
2. Adicionar retry com exponential backoff para Pearch API
3. Implementar circuit breaker pattern via library (Polly ou similar)
4. Rate limiting: 100 req/min por empresa

---

### 3. Segurança

#### a) Diagnóstico do Estado Atual
```
✅ Autenticação: JWT com access_token em localStorage
✅ Autorização: Token verificado em cada request
⚠️ Multi-tenancy: company_id presente mas não validado em todos endpoints
⚠️ XSS: React escapa por padrão, mas dangerouslySetInnerHTML em alguns locais
✅ CSRF: Não aplicável (API stateless)
⚠️ SQL Injection: SQLAlchemy ORM protege, mas raw queries existem
⚠️ IDOR: Alguns endpoints não validam ownership
```

#### b) Riscos e Impactos
- Candidato de empresa A pode ser acessado por empresa B se ID conhecido
- Ausência de audit log para ações críticas (exclusão, bulk actions)
- Secrets expostos em logs de desenvolvimento

#### c) Recomendações Concretas
1. Middleware global de validação `company_id` em TODOS os endpoints
2. Implementar audit trail para: delete, bulk_update, opinion_create
3. Adicionar row-level security no PostgreSQL
4. Sanitizar inputs em campos de busca livre

---

### 4. Backend e Frontend (Contratos)

#### a) Diagnóstico do Estado Atual

**Endpoints Principais do Funil:**
| Endpoint | Método | Payload/Response |
|----------|--------|------------------|
| `/search/candidates` | POST | SearchRequestDTO → UnifiedSearchResponseDTO |
| `/search/candidates/local` | GET | query params → CandidateListResponse |
| `/search/candidates/import` | POST | ImportCandidatesRequest → ImportCandidatesResponse |
| `/candidates/{id}` | GET | - → CandidateDetailDTO |
| `/candidates/{id}/favorite` | POST/PUT | note, is_pinned → status |
| `/opinions/candidate/{id}/summary` | GET | - → OpinionSummaryDTO |
| `/wsi/generate-questions` | POST | WSIGenerateRequest → WSIQuestionsResponse |

#### b) Riscos e Impactos
- Versionamento de API inexistente (`/api/v1/` existe mas sem v2)
- Status codes inconsistentes (alguns retornam 200 com `success: false`)
- Payloads com campos snake_case e camelCase misturados

#### c) Recomendações Concretas
1. Padronizar todos os payloads para snake_case
2. Implementar versionamento: `/api/v2/` para mudanças breaking
3. Documentar OpenAPI/Swagger completo
4. Criar DTOs de response padronizados: `{ data, meta, errors }`

---

### 5. Banco de Dados

#### a) Diagnóstico do Estado Atual
**Tabelas Principais:**
```sql
candidates (id, company_id, name, email, phone, linkedin_url, ...)
candidate_work_history (id, candidate_id, company_name, title, ...)
lia_opinions (id, candidate_id, job_vacancy_id, score, archetype, ...)
candidate_favorites (id, candidate_id, user_id, note, is_pinned, ...)
candidate_lists (id, company_id, name, ...)
candidate_list_items (list_id, candidate_id, ...)
job_vacancies (id, company_id, title, status, ...)
```

#### b) Riscos e Impactos
- Índices faltando em `candidates.company_id` + `candidates.email`
- `lia_opinions` pode ter duplicatas (versioning não atômico)
- `candidate_work_history` sem índice em `candidate_id`
- Queries N+1 em listagens de candidatos

#### c) Recomendações Concretas
```sql
CREATE INDEX idx_candidates_company_email ON candidates(company_id, email);
CREATE INDEX idx_work_history_candidate ON candidate_work_history(candidate_id);
CREATE INDEX idx_opinions_candidate_type ON lia_opinions(candidate_id, opinion_type, is_current);
```

---

### 6. Integração Interna com Outros Módulos

#### a) Diagnóstico do Estado Atual
```
Funil de Talentos ←→ Gestão de Vagas (jobs-page.tsx)
Funil de Talentos ←→ Chat LIA (chat-page.tsx)
Funil de Talentos ←→ Pareceres (opinions.py)
Funil de Talentos ←→ WSI Screening (wsi.py)
Funil de Talentos ←→ Email Templates (email_templates.py)
Funil de Talentos ←→ Listas de Candidatos (candidate_lists.py)
Funil de Talentos ←→ Dashboard KPIs (dashboards-page.tsx)
```

#### b) Riscos e Impactos
- Eventos não são publicados (ex: candidato adicionado a vaga)
- Dependência circular: Funil importa componentes de Vagas e vice-versa
- Ausência de event bus para comunicação desacoplada

#### c) Recomendações Concretas
1. Implementar event bus (RabbitMQ ou Redis Pub/Sub)
2. Eventos: `candidate.created`, `candidate.favorited`, `opinion.generated`
3. Extrair componentes compartilhados para `/components/shared/`

---

### 7. Arquitetura Geral

#### a) Diagnóstico do Estado Atual
```
┌──────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                        │
├──────────────────────────────────────────────────────────────┤
│ /app/funil/page.tsx → CandidatesPage (12.000 linhas)         │
│   ├── ExpandableAIPrompt (busca com IA)                      │
│   ├── UnifiedCandidateTable (tabela de resultados)           │
│   ├── CandidatePreview (preview lateral)                     │
│   ├── SmartSearchInput (input inteligente)                   │
│   ├── AdvancedFiltersModal (filtros)                         │
│   ├── WSITextScreeningModal (triagem WSI)                    │
│   ├── UnifiedCommunicationModal (comunicação)                │
│   └── Tabs: Favoritos, Histórico, Listas, Buscas Salvas      │
└──────────────────────────────────────────────────────────────┘
                              ↓ /api/backend-proxy/*
┌──────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                         │
├──────────────────────────────────────────────────────────────┤
│ /api/v1/search/* → Pearch + Local hybrid search              │
│ /api/v1/candidates/* → CRUD candidatos                       │
│ /api/v1/opinions/* → Pareceres LIA                           │
│ /api/v1/wsi/* → Work Sample Interview                        │
│ /api/v1/candidate_lists/* → Listas de candidatos             │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                     AI AGENTS (LangGraph)                     │
├──────────────────────────────────────────────────────────────┤
│ RecruiterAssistantAgent → Busca e filtros inteligentes       │
│ OpinionGeneratorAgent → Geração de pareceres                 │
│ WSIInterviewerAgent → Condução de entrevistas WSI            │
└──────────────────────────────────────────────────────────────┘
```

#### b) Riscos e Impactos
- Monolito frontend dificulta manutenção e testes
- Agentes de IA acoplados a componentes React
- Falta de camada de serviço no frontend

#### c) Recomendações Concretas
1. Dividir CandidatesPage em 4 workspaces:
   - SearchWorkspace (busca e filtros)
   - ResultsWorkspace (tabela e paginação)
   - PreviewWorkspace (preview lateral)
   - ActionsWorkspace (modais e bulk actions)
2. Extrair lógica de IA para hooks dedicados
3. Implementar service layer no frontend

---

### 8. Sincronização entre Back, Front, Dados, IA e Serviços

#### a) Diagnóstico do Estado Atual
```
Fluxo de Busca:
1. Usuário digita query → SmartSearchInput
2. Frontend chama /search/candidates
3. Backend executa busca local + Pearch em paralelo
4. Resultados mergeados e rankeados
5. Frontend atualiza estado local
6. Preview carrega detalhes sob demanda

Problemas:
- Estado local (localStorage) pode divergir do backend
- Busca Pearch pode timeout sem retry
- Importação de candidatos Pearch não é atômica
```

#### b) Riscos e Impactos
- Candidatos favoritos podem aparecer/desaparecer inconsistentemente
- Buscas salvas em localStorage perdidas em outros dispositivos
- Sem optimistic updates (UX lenta)

#### c) Recomendações Concretas
1. Migrar localStorage para API + cache local
2. Implementar optimistic updates com rollback
3. Adicionar sync background a cada 5 minutos
4. WebSocket para atualizações real-time (opinião gerada, status mudou)

---

### 9. Uso de Dados Mockados

#### a) Diagnóstico do Estado Atual
```
✅ Buscas usam dados reais do PostgreSQL
✅ Candidatos Pearch são reais da API
⚠️ Work history pode ser gerado quando ausente (generateWorkHistory)
⚠️ Salários são estimados com fórmula mock
❌ Alguns testes usam hardcoded data sem seed
```

#### b) Riscos e Impactos
- Histórico de trabalho gerado pode confundir recrutadores
- Salários estimados podem gerar expectativas incorretas

#### c) Recomendações Concretas
1. Marcar visualmente dados estimados/gerados com badge "Estimado"
2. Seed database com fixtures realistas para testes
3. Remover geração de dados em produção

---

### 10. Testes Automatizados

#### a) Diagnóstico do Estado Atual
```
Frontend:
- Jest configurado mas poucos testes
- Storybook com stories para alguns componentes
- E2E: Não implementado

Backend:
- Pytest configurado
- Cobertura estimada: ~20%
- Integração: Alguns endpoints testados
```

#### b) Riscos e Impactos
- Regressões frequentes em refatorações
- Mudanças em um componente quebram outros silenciosamente
- Deploy sem confiança

#### c) Recomendações Concretas
| Tipo | Meta de Cobertura | Prioridade |
|------|-------------------|------------|
| Unit (hooks) | 80% | Alta |
| Integration (API) | 70% | Alta |
| E2E (fluxos críticos) | 50% | Média |
| Visual (Storybook/Chromatic) | 100% componentes | Média |

---

### 11. Documentação Básica da Feature

#### a) Diagnóstico do Estado Atual
- `replit.md` documenta overview do sistema
- Inline comments em alguns arquivos
- Storybook documenta alguns componentes
- API: Sem OpenAPI/Swagger completo

#### b) Riscos e Impactos
- Onboarding de novos desenvolvedores demorado
- Decisões arquiteturais não documentadas
- APIs sem especificação formal

#### c) Recomendações Concretas
1. Criar `docs/features/FUNIL_DE_TALENTOS.md` (este documento)
2. Gerar OpenAPI spec via FastAPI
3. Documentar todos os componentes no Storybook
4. ADR (Architecture Decision Records) para decisões importantes

---

### 12. Performance

#### a) Diagnóstico do Estado Atual
```
Gargalos Identificados:
- CandidatesPage (12k linhas) → bundle size elevado
- Tabela sem virtualização (>1000 rows = lag)
- Preview carrega todos os dados (não lazy)
- Busca Pearch pode levar 5-15s
- Queries N+1 em listagens
```

#### b) Riscos e Impactos
- Time to Interactive > 5s em conexões lentas
- Scroll stuttering com muitos candidatos
- Timeout em buscas complexas

#### c) Recomendações Concretas
1. Code splitting: dividir CandidatesPage em chunks
2. Virtualização: react-virtual para tabelas grandes
3. Lazy loading: preview carrega seções sob demanda
4. Cache: Redis para buscas recentes
5. Pagination: cursor-based ao invés de offset

---

### 13. Acessibilidade

#### a) Diagnóstico do Estado Atual
```
✅ Radix UI primitives (acessíveis por padrão)
✅ Labels em inputs
⚠️ Contraste: alguns textos gray-400 em bg branco
⚠️ Focus visible: inconsistente
❌ Skip links: Ausentes
❌ Screen reader: Não testado
```

#### b) Riscos e Impactos
- Usuários com deficiência visual podem não usar a plataforma
- Não compliance com WCAG 2.1 AA

#### c) Recomendações Concretas
1. Audit com axe-core ou Lighthouse
2. Aumentar contraste mínimo para 4.5:1
3. Implementar skip links
4. Testar com NVDA/VoiceOver

---

### 14. Revisão de Código

#### a) Diagnóstico do Estado Atual
```
Clean Code: ⚠️ Arquivo principal muito extenso
DRY: ⚠️ Funções de formatação duplicadas
KISS: ⚠️ Lógica complexa em componentes
SOLID: ❌ Violações frequentes (componentes fazem muita coisa)
```

#### b) Riscos e Impactos
- Manutenção cara e arriscada
- Bugs difíceis de rastrear
- Onboarding demorado

#### c) Recomendações Concretas
1. Extrair para funções utilitárias: `formatDate`, `formatCurrency`, `getScoreColor`
2. Custom hooks para cada domínio: `useCandidateSearch`, `useCandidatePreview`
3. Limitar arquivos a 500 linhas máximo

---

### 15. Estrutura Modular

#### a) Diagnóstico do Estado Atual
```
plataforma-lia/src/
├── app/funil/page.tsx (wrapper)
├── components/
│   ├── pages/candidates-page.tsx (12k linhas - PROBLEMA)
│   ├── candidate-preview.tsx (4.8k linhas)
│   ├── talent-funnel-tabs/ (7 tabs)
│   ├── modals/ (9 modais)
│   ├── search/ (10 componentes)
│   └── wsi/ (5 componentes)
├── hooks/ (16 hooks)
└── services/lia-api.ts (2.1k linhas)
```

#### b) Riscos e Impactos
- Arquivos gigantes = merge conflicts frequentes
- Difícil testar isoladamente
- Import circular potencial

#### c) Recomendações Concretas

**Estrutura Proposta:**
```
src/features/talent-funnel/
├── components/
│   ├── SearchWorkspace/
│   │   ├── SearchWorkspace.tsx
│   │   ├── SmartSearchInput.tsx
│   │   └── AdvancedFilters.tsx
│   ├── ResultsWorkspace/
│   │   ├── ResultsWorkspace.tsx
│   │   ├── CandidateTable.tsx
│   │   └── TablePagination.tsx
│   ├── PreviewWorkspace/
│   │   ├── PreviewWorkspace.tsx
│   │   ├── ProfileSection.tsx
│   │   ├── ExperienceSection.tsx
│   │   └── OpinionSection.tsx
│   └── ActionsWorkspace/
│       ├── BulkActions.tsx
│       └── ActionModals/
├── hooks/
│   ├── useCandidateSearch.ts
│   ├── useCandidatePreview.ts
│   ├── useBulkActions.ts
│   └── useFavorites.ts
├── services/
│   ├── searchService.ts
│   ├── candidateService.ts
│   └── opinionService.ts
├── types/
│   └── index.ts
└── index.ts
```

---

### 16. Documentação Detalhada para Tarefas

#### a) Diagnóstico do Estado Atual
- Histórias de usuário não formalizadas
- Regras de negócio inline no código
- Cálculos de score não documentados

#### b) Riscos e Impactos
- Desenvolvedores interpretam requisitos diferentemente
- Testes incompletos por falta de specs

#### c) Recomendações Concretas
Ver seção 17 (Cards de Especificação)

---

### 17. Cards de Especificação (Estilo Jira)

Veja **Seção 4 do Documento Final Consolidado** para lista completa de tasks.

**Exemplo de Card:**

```
TÍTULO: [FUN-001] Modularizar CandidatesPage em 4 Workspaces

DESCRIÇÃO:
Dividir o arquivo candidates-page.tsx (12k linhas) em 4 componentes 
independentes para melhorar manutenibilidade e testabilidade.

TIPO: Tech Debt

HISTÓRIA:
Como desenvolvedor, preciso que o código do Funil esteja modularizado
para facilitar manutenção e evitar merge conflicts.

REGRAS DE NEGÓCIO:
- Cada workspace deve ser independente
- Estado compartilhado via Context ou Zustand
- Props drilling máximo: 2 níveis

RISCOS:
- Regressão visual durante refatoração
- Estado pode quebrar se não migrado corretamente

DEPENDÊNCIAS:
- Nenhuma

CRITÉRIOS DE ACEITAÇÃO:
- [ ] SearchWorkspace funciona isoladamente
- [ ] ResultsWorkspace funciona isoladamente
- [ ] PreviewWorkspace funciona isoladamente
- [ ] ActionsWorkspace funciona isoladamente
- [ ] Testes passando
- [ ] Visual regression aprovado

ESTIMATIVA:
- Ideal: 3 dias
- Realista: 5 dias
- Pessimista: 8 dias
```

---

### 18. Roadmap em Formato de Fluxos

```
FASE 1: Estabilização (Semanas 1-4)
├── [1.1] Modularizar CandidatesPage
├── [1.2] Extrair hooks dedicados
├── [1.3] Consolidar estado (remover localStorage)
└── [1.4] Adicionar testes críticos

FASE 2: Otimização (Semanas 5-8)
├── [2.1] Implementar virtualização de tabela
├── [2.2] Adicionar cache Redis
├── [2.3] Optimistic updates
└── [2.4] Code splitting

FASE 3: Padronização API (Semanas 9-12)
├── [3.1] Documentar OpenAPI completo
├── [3.2] Padronizar responses
├── [3.3] Versionamento v2
└── [3.4] Implementar adapters para Rails

FASE 4: Migração Rails + Vue (Semanas 13-24)
├── [4.1] Setup Rails engines
├── [4.2] Criar modelos ActiveRecord
├── [4.3] Implementar Vue components
└── [4.4] Migração incremental por workspace
```

---

### 19. Diagrama da Jornada da Feature

**Visão do Usuário:**
```
1. Recrutador acessa /funil
2. Digita busca natural: "Desenvolvedor Python São Paulo 5 anos"
3. Sistema sugere modo de busca e fonte (Local/Pearch)
4. Resultados aparecem na tabela
5. Clica em candidato → Preview abre
6. Analisa perfil, experiência, skills
7. Gera Parecer LIA (se dados suficientes)
8. Adiciona aos favoritos ou lista
9. Envia comunicação (email/WhatsApp)
10. Agenda entrevista WSI
```

**Visão do Sistema:**
```
1. Next.js renderiza CandidatesPage
2. SmartSearchInput processa query
3. API /search/candidates chamada
4. Backend: query → Pearch + Local em paralelo
5. Resultados mergeados e rankeados por relevância
6. Frontend atualiza tabela
7. Clique → /candidates/{id} carrega detalhes
8. Parecer → /opinions endpoint com Claude AI
9. Favoritos → localStorage + API sync
10. Comunicação → /email-templates ou /communications
```

---

### 20. Sequência Lógica de Desenvolvimento

**MVP (Semanas 1-4):**
1. Modularização do monolito
2. Testes para fluxos críticos
3. Fix de bugs conhecidos

**Incremento 1 (Semanas 5-8):**
1. Performance (virtualização, cache)
2. Consistência de estado
3. UX improvements

**Incremento 2 (Semanas 9-12):**
1. Padronização de APIs
2. Documentação completa
3. Preparação para migração

**Incremento 3 (Semanas 13-24):**
1. Rails engines
2. Vue components
3. Migração incremental

---

### 21. Priorização no Produto

| Feature/Fix | Valor | Complexidade | Risco | Prioridade |
|-------------|-------|--------------|-------|------------|
| Modularizar monolito | Alto | Alto | Médio | P0 |
| Cache de buscas | Alto | Médio | Baixo | P0 |
| Virtualização tabela | Alto | Médio | Baixo | P1 |
| Testes automatizados | Alto | Médio | Baixo | P1 |
| Documentação API | Médio | Baixo | Baixo | P1 |
| Migração Vue | Alto | Alto | Alto | P2 |

---

### 22. Tempo Estimado de Desenvolvimento

| Fase | Ideal | Realista | Pessimista |
|------|-------|----------|------------|
| Estabilização | 3 sem | 4 sem | 6 sem |
| Otimização | 3 sem | 4 sem | 6 sem |
| Padronização API | 3 sem | 4 sem | 5 sem |
| Migração Rails+Vue | 8 sem | 12 sem | 16 sem |
| **TOTAL** | **17 sem** | **24 sem** | **33 sem** |

---

### 23. Documento de Padrão de Design Consolidado

Veja: `docs/DESIGN_STANDARDS.md`

**Design Tokens Chave:**
```typescript
export const designTokens = {
  colors: {
    primary: '#60BED1',
    primaryHover: '#50a3b8',
    textTitle: '#1f2937', // gray-800
    textBody: '#4b5563', // gray-600
    textMuted: '#6b7280', // gray-500
    borderLight: '#f3f4f6', // gray-100
    borderMedium: '#e5e7eb', // gray-200
  },
  typography: {
    fontTitle: '"Source Serif 4", serif',
    fontBody: '"Open Sans", sans-serif',
    sizeTitle: '13px',
    sizeBody: '11px',
    sizeSmall: '10px',
  },
  spacing: {
    cardPadding: '0.625rem', // p-2.5
    sectionGap: '0.75rem', // gap-3
  },
  shadows: {
    card: 'shadow-sm',
  },
  borders: {
    card: 'border border-gray-100 rounded-lg',
  }
}
```

---

### 24. Direcionamento Técnico para Rails + Vue + Nuxt + Vuetify

**Rails Backend:**
```ruby
# app/engines/candidate_search/
module CandidateSearch
  class Engine < ::Rails::Engine
    isolate_namespace CandidateSearch
  end
end

# app/models/candidate.rb
class Candidate < ApplicationRecord
  belongs_to :company
  has_many :work_experiences
  has_many :opinions, class_name: 'LiaOpinion'
  has_many :list_memberships
  
  scope :for_company, ->(company_id) { where(company_id: company_id) }
end

# app/controllers/api/v1/candidates_controller.rb
class Api::V1::CandidatesController < ApplicationController
  def index
    candidates = current_company.candidates
      .includes(:work_experiences, :opinions)
      .page(params[:page])
    
    render json: CandidateSerializer.new(candidates).serializable_hash
  end
end
```

**Vue + Nuxt Frontend:**
```vue
<!-- pages/funil/index.vue -->
<template>
  <v-container fluid>
    <SearchWorkspace @search="handleSearch" />
    <ResultsWorkspace 
      :candidates="candidates" 
      @select="handleSelect" 
    />
    <PreviewDrawer 
      v-if="selectedCandidate"
      :candidate="selectedCandidate"
    />
  </v-container>
</template>

<script setup>
import { useCandidateSearch } from '@/composables/useCandidateSearch'

const { candidates, search, isLoading } = useCandidateSearch()
</script>
```

**Pinia Store:**
```typescript
// stores/candidates.ts
export const useCandidatesStore = defineStore('candidates', {
  state: () => ({
    items: [] as Candidate[],
    selectedId: null as string | null,
    filters: {} as SearchFilters,
    isLoading: false,
  }),
  
  actions: {
    async search(query: string) {
      this.isLoading = true
      try {
        const response = await $fetch('/api/v1/candidates/search', {
          method: 'POST',
          body: { query, ...this.filters }
        })
        this.items = response.data
      } finally {
        this.isLoading = false
      }
    }
  }
})
```

---

### 25. Integrações via API, Webhook ou MCP

**APIs Consumidas:**
| Integração | Tipo | Auth | Retry | Idempotente |
|------------|------|------|-------|-------------|
| Pearch AI | REST | API Key | ❌ Não | ❌ Não |
| Claude (Anthropic) | REST | API Key | ✅ Sim | ✅ Sim |
| Google Gemini | REST | API Key | ✅ Sim | ✅ Sim |
| Microsoft Graph | OAuth2 | Bearer | ✅ Sim | ✅ Sim |

**Webhooks Expostos:**
- Nenhum implementado (oportunidade de melhoria)

**Recomendações:**
1. Adicionar retry com exponential backoff para Pearch
2. Implementar webhooks para: `candidate.created`, `opinion.generated`
3. Rate limiting: 10 req/s para Pearch, 100 req/min por empresa

---

### 26. Uso de Inteligência Artificial

#### a) Diagnóstico do Estado Atual

**Uso de IA no Funil:**
| Feature | Modelo | Input | Output | Custo |
|---------|--------|-------|--------|-------|
| Parecer LIA | Claude 3.5 Sonnet | Perfil candidato | Score + Análise | ~$0.02/req |
| WSI Questions | Claude 3.5 Sonnet | Vaga + Perfil | 5 perguntas | ~$0.03/req |
| Query Parsing | Claude 3.5 Haiku | Texto busca | Entidades estruturadas | ~$0.001/req |
| Transcrição | Google Gemini | Áudio | Texto | ~$0.01/min |

#### b) Riscos e Impactos
- Custos podem escalar rapidamente com uso intenso
- Latência de IA (2-5s) impacta UX
- Fallback não implementado para todos os casos

#### c) Recomendações Concretas
1. Cache de respostas IA por perfil (TTL 24h)
2. Fallback: se Claude falhar, retornar "Análise indisponível"
3. Rate limiting por empresa: 1000 req IA/dia
4. Monitoramento de custos em tempo real

---

### 27. Separação Back x Front nos Fluxos

| Fluxo | Frontend | Backend |
|-------|----------|---------|
| Busca Natural | Parse query, UI feedback | Executar busca, rankear |
| Filtros | UI de seleção | Aplicar filtros SQL |
| Preview | Renderizar dados | Carregar candidato + relations |
| Parecer LIA | Exibir resultado | Gerar com Claude AI |
| Favoritos | Toggle UI, optimistic | Persistir, notificar |
| Bulk Actions | Seleção múltipla | Executar em batch |
| Importar Pearch | Confirmar seleção | Upsert candidatos |

---

### 28. Consistência Tailwind ↔ Vuetify

| Tailwind | Vuetify Equivalent |
|----------|-------------------|
| `bg-[#60BED1]` | `color="primary"` (theme) |
| `shadow-sm` | `elevation="1"` |
| `rounded-lg` | `rounded="lg"` |
| `border-gray-100` | `:outlined="true"` + CSS var |
| `text-[13px] font-semibold` | `class="text-subtitle-1"` |
| `p-2.5` | `class="pa-2"` |
| `gap-3` | `class="ga-3"` |
| `flex items-center` | `class="d-flex align-center"` |

**Vuetify Theme Config:**
```typescript
// vuetify.config.ts
export default {
  theme: {
    themes: {
      light: {
        colors: {
          primary: '#60BED1',
          secondary: '#6B7280',
          accent: '#60BED1',
          error: '#EF4444',
          warning: '#F59E0B',
          success: '#10B981',
        }
      }
    }
  }
}
```

---

### 29. Requisitos Funcionais

| ID | Requisito | Status |
|----|-----------|--------|
| RF01 | Buscar candidatos por texto natural | ✅ Implementado |
| RF02 | Filtrar por localização, skills, experiência | ✅ Implementado |
| RF03 | Visualizar preview de candidato | ✅ Implementado |
| RF04 | Gerar Parecer LIA automaticamente | ✅ Implementado |
| RF05 | Adicionar candidato aos favoritos | ✅ Implementado |
| RF06 | Criar e gerenciar listas de candidatos | ✅ Implementado |
| RF07 | Busca híbrida (Local + Pearch) | ✅ Implementado |
| RF08 | Importar candidatos Pearch para base local | ✅ Implementado |
| RF09 | Enviar comunicação (email/WhatsApp) | ✅ Implementado |
| RF10 | Iniciar triagem WSI | ✅ Implementado |
| RF11 | Comparar candidatos lado a lado | ✅ Implementado |
| RF12 | Exportar lista de candidatos | ⚠️ Parcial |
| RF13 | Bulk actions (favoritar, adicionar lista) | ✅ Implementado |
| RF14 | Salvar buscas para reuso | ⚠️ localStorage only |

---

### 30. Requisitos Não Funcionais

| ID | Requisito | Meta | Status |
|----|-----------|------|--------|
| RNF01 | Tempo de resposta busca | < 3s (local), < 10s (Pearch) | ⚠️ Pearch pode exceder |
| RNF02 | Disponibilidade | 99.5% | ✅ OK |
| RNF03 | Candidatos por empresa | Até 100.000 | ⚠️ Não testado |
| RNF04 | Concurrent users | 100 por empresa | ⚠️ Não testado |
| RNF05 | Segurança multi-tenant | Isolamento total | ⚠️ Parcial |
| RNF06 | Audit trail | Todas ações críticas | ❌ Não implementado |
| RNF07 | LGPD compliance | Opt-out, quarentena | ⚠️ Parcial |
| RNF08 | Acessibilidade | WCAG 2.1 AA | ⚠️ Parcial |

---

### 31. Riscos e Recomendações Finais

**Riscos Técnicos:**
| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Regressão em refatoração | Alta | Alto | Testes + Visual regression |
| Performance com muitos dados | Média | Alto | Virtualização + Cache |
| Integração IA falhar | Baixa | Médio | Fallback + Retry |
| Migração Rails quebrar fluxos | Média | Alto | Adapters + Migração incremental |

**Riscos de Negócio:**
| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Custos IA escalarem | Média | Médio | Rate limiting + Cache |
| Dados Pearch desatualizados | Baixa | Baixo | Freshness flag |
| Compliance LGPD | Média | Alto | Audit + Opt-out |

**Riscos Operacionais:**
| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Deploy quebrar produção | Média | Alto | Feature flags + Rollback |
| Timeout em buscas | Média | Médio | Circuit breaker |
| Perda de dados localStorage | Alta | Médio | Migrar para API |

---

### 32. Integração Figma + Chromatic (Validação Visual)

#### a) Componentes Mapeados
| Componente | Figma Frame | Storybook Story | Chromatic Snapshot |
|------------|-------------|-----------------|-------------------|
| CandidatePreview | ✅ Existe | ✅ Existe | ⚠️ Não configurado |
| SmartSearchInput | ⚠️ Parcial | ❌ Falta | ❌ Falta |
| CandidateTable | ⚠️ Parcial | ⚠️ Parcial | ❌ Falta |
| OpinionCard | ✅ Existe | ❌ Falta | ❌ Falta |
| AdvancedFiltersModal | ❌ Falta | ❌ Falta | ❌ Falta |

#### b) Riscos Visuais na Migração
1. Tailwind utilities → Vuetify classes pode quebrar layout
2. Shadcn components não têm equivalente direto em Vuetify
3. Responsividade pode divergir

#### c) Recomendações
1. Configurar Chromatic para CI/CD
2. Criar stories para TODOS os componentes do Funil
3. Manter Storybook como source of truth durante migração
4. Visual diff obrigatório antes de merge

---

## 📘 DOCUMENTO FINAL CONSOLIDADO

---

## 1. Resumo Executivo

### O que é a Feature
O Funil de Talentos é o módulo central de busca e gestão de candidatos da Plataforma LIA, oferecendo busca híbrida (local + Pearch AI), preview de candidatos, pareceres IA, e ações em lote.

### Principais Riscos
1. Monolito frontend de 12.000 linhas
2. Estado fragmentado (localStorage + API)
3. Contratos API não padronizados
4. Multi-tenancy inconsistente

### Esforço Estimado
- **Realista:** 24 semanas para refatoração completa + migração

### Recomendação Estratégica
Implementar refatoração progressiva em 4 fases, priorizando modularização e testes antes da migração Rails + Vue.

---

## 2. Visão Técnica Completa

### Arquitetura Atual
- **Frontend:** Next.js 14 + React + Tailwind + shadcn/ui
- **Backend:** FastAPI + SQLAlchemy + LangGraph
- **Database:** PostgreSQL (Neon via Replit)
- **AI:** Claude 3.5 Sonnet + Google Gemini
- **Search:** Pearch AI + Local PostgreSQL

### Arquitetura Alvo
- **Frontend:** Vue 3 + Nuxt 3 + Vuetify 3
- **Backend:** Ruby on Rails 7 + Sidekiq
- **Database:** PostgreSQL com row-level security
- **AI:** LangGraph workflows via ActionCable

### Contratos de API
Veja seção 4 (Backend e Frontend Contratos)

### Modelos de Dados
Veja seção 5 (Banco de Dados)

---

## 3. Lista Estruturada de Tasks

### FASE 1: Estabilização

#### FUN-001: Modularizar CandidatesPage
- **Tipo:** Tech Debt
- **Dependências:** Nenhuma
- **Estimativa:** 3/5/8 dias
- **AC:** 4 workspaces independentes funcionando

#### FUN-002: Extrair Custom Hooks
- **Tipo:** Tech Debt
- **Dependências:** FUN-001
- **Estimativa:** 2/3/5 dias
- **AC:** Hooks para search, preview, favorites, bulk actions

#### FUN-003: Migrar localStorage para API
- **Tipo:** Tech Debt
- **Dependências:** FUN-002
- **Estimativa:** 3/5/7 dias
- **AC:** Histórico e buscas salvas persistidos no backend

#### FUN-004: Adicionar Testes Críticos
- **Tipo:** Tech Debt
- **Dependências:** FUN-001, FUN-002
- **Estimativa:** 5/8/12 dias
- **AC:** 70% cobertura em hooks, 50% em componentes

### FASE 2: Otimização

#### FUN-005: Implementar Virtualização de Tabela
- **Tipo:** Feature
- **Dependências:** FUN-001
- **Estimativa:** 2/3/5 dias
- **AC:** Scroll suave com 10.000+ candidatos

#### FUN-006: Adicionar Cache Redis
- **Tipo:** Feature
- **Dependências:** Nenhuma
- **Estimativa:** 3/5/7 dias
- **AC:** Buscas cacheadas por 5min, latência reduzida 50%

#### FUN-007: Optimistic Updates
- **Tipo:** Feature
- **Dependências:** FUN-003
- **Estimativa:** 2/3/4 dias
- **AC:** Favoritos e listas atualizam instantaneamente

#### FUN-008: Code Splitting
- **Tipo:** Tech Debt
- **Dependências:** FUN-001
- **Estimativa:** 2/3/4 dias
- **AC:** Bundle inicial reduzido 40%

### FASE 3: Padronização API

#### FUN-009: Documentar OpenAPI
- **Tipo:** Docs
- **Dependências:** Nenhuma
- **Estimativa:** 3/5/7 dias
- **AC:** Swagger UI disponível, todos endpoints documentados

#### FUN-010: Padronizar Responses
- **Tipo:** Tech Debt
- **Dependências:** FUN-009
- **Estimativa:** 3/5/7 dias
- **AC:** Todos responses seguem `{ data, meta, errors }`

#### FUN-011: Implementar Versionamento v2
- **Tipo:** Feature
- **Dependências:** FUN-010
- **Estimativa:** 2/3/5 dias
- **AC:** /api/v2/ disponível, v1 mantido por 6 meses

#### FUN-012: Criar Adapters Rails
- **Tipo:** Feature
- **Dependências:** FUN-010, FUN-011
- **Estimativa:** 5/8/12 dias
- **AC:** Adapters mapeiam FastAPI → Rails serializers

### FASE 4: Migração Rails + Vue

#### FUN-013 a FUN-024: Tasks de Migração
(12 tasks detalhadas para migração incremental por workspace)

---

## 4. Sugestões Avançadas de Melhoria

1. **Real-time Updates:** WebSocket para notificar quando opinião é gerada
2. **AI Agents Dashboard:** Monitoramento de custos e latência de IA
3. **Candidate Insights:** Predição de probabilidade de aceitar oferta
4. **Smart Deduplication:** IA identifica candidatos duplicados
5. **Bulk WSI:** Enviar triagem WSI para múltiplos candidatos
6. **Integration Hub:** Conectar com LinkedIn, Indeed, Glassdoor
7. **Mobile App:** Versão PWA para recrutadores em campo
8. **Voice Search:** Busca por voz com Gemini transcription

---

*Documento gerado em 10/12/2025 - Versão 1.0*
