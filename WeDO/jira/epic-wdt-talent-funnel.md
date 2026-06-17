# FUNIL DE TALENTOS — CARDS WDT (WeDo Talent Search Optimization)

**Data:** Fevereiro 2026  
**Versão:** 1.1  
**Última Atualização:** 08 Fevereiro 2026  
**Status:** Documento de Referência para Desenvolvimento  
**Origem:** Análise metodológica com André (especialista em busca) + reunião de alinhamento Paulo/Anderson

> **Total de Cards:** 27 cards ativos (WDT-001 a WDT-030, excl. WDT-017/019/020 cancelados) — 7 incorporados ao Épico 3 como MAP-007 a MAP-013  
> **Story Points Total:** 145 SP  
> **Horas Estimadas:** 270 horas  
> **Fases:** 6 (Quick Wins → Docs & Infra)  
> **MVP:** 7 cards (23 SP) no Épico 3 (WDT-001 a WDT-004, WDT-005, WDT-006, WDT-007 → MAP-007 a MAP-013)  
> **Pós-MVP:** 20 cards (122 SP) nos Épicos 16-19

---

## MAPA DE AMBIENTES

| Aspecto | Replit (Protótipo/Referência) | Produção (Equipe Externa) |
|---------|-------------------------------|---------------------------|
| **Frontend** | React 18 + Next.js + TypeScript | Vue.js 3 + Nuxt 3 + TypeScript |
| **UI Framework** | Tailwind CSS + shadcn/ui + Radix | Vuetify 3 + Design Tokens LIA |
| **State Management** | React Context + hooks | Pinia |
| **Backend Principal** | — (protótipo apenas) | Ruby on Rails 7.x |
| **API** | Python FastAPI (agentes IA) | Rails API + Python FastAPI (IA) |
| **Banco de Dados** | PostgreSQL (Neon) | PostgreSQL + Elasticsearch + PG Vector |
| **Busca** | Simulada/mockada | Elasticsearch 8.x + PG Vector |
| **Background Jobs** | — | Sidekiq + Redis + RabbitMQ |
| **IA/Agentes** | LangGraph + Gemini (FastAPI) | LangGraph + LangChain + Gemini (FastAPI) |
| **LLM** | Gemini 2.5 Flash | Gemini 2.5 Flash (MVP), Claude futuro |
| **Cache** | — | Redis |
| **Mensageria** | — | RabbitMQ |
| **Testes** | Jest + Testing Library | RSpec (Rails) + Vitest (Vue) + pytest (Python) |

### Implicações para os Prompts de IA

Os prompts incluídos em cada card consideram que:
1. **Frontend**: O protótipo Replit (React) serve como referência de **comportamento e UX**, mas o código deve ser escrito em **Vue.js 3 + Vuetify 3**
2. **Backend**: Rails é o backend principal. Python/FastAPI é usado APENAS para agentes IA e processamento LLM
3. **Busca**: Elasticsearch e PG Vector são infraestrutura real — não são simulados
4. **Jobs assíncronos**: Usar Sidekiq (Rails) para jobs de negócio, RabbitMQ para comunicação entre serviços
5. **Padrões Rails**: Service Objects, Form Objects, Concerns, RESTful routes com versionamento (/api/v1/)
6. **Padrões Vue**: Composition API, composables, single-file components (.vue)

---

## TEMPLATE DO BLOCO DE CONTEXTO PARA PROMPTS IA

Cada card contém um prompt para IA (Cursor/VSCode) que começa com este bloco padrão:

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3 + Nuxt 3
- Banco: PostgreSQL + Elasticsearch 8.x + PG Vector (pgvector extension)
- Background Jobs: Sidekiq + Redis
- Mensageria: RabbitMQ (comunicação entre serviços)
- IA/Agentes: Python 3.11 + FastAPI + LangGraph + LangChain + Gemini 2.5 Flash
- Cache: Redis
- Testes: RSpec (Rails) + Vitest (Vue) + pytest (Python)
- API: RESTful com versionamento /api/v1/
- Autenticação: JWT via WorkOS SSO
- Multi-tenant: Scoping por company_id em todas as queries
- Referência visual: Protótipo React/Next.js/Tailwind no Replit (copiar COMPORTAMENTO, não código)

PADRÕES DE CÓDIGO:
- Rails: Service Objects para lógica de negócio, Concerns para compartilhamento, Serializers para API
- Vue: Composition API (<script setup>), composables para lógica reutilizável, Pinia para state
- Python: Classes com typing, async/await, Pydantic models
- Todos: TypeScript/tipagem estrita, sem any/untyped
```

---

## RESUMO EXECUTIVO POR FASE

| Fase | Cards | SP | Horas | Sprints | Prioridade | Épico | Timing |
|------|-------|----|-------|---------|------------|-------|--------|
| **Fase 1 - Quick Wins** | 8 (WDT-001 a 008) | 28 | 46 | 1-2 | Critical | 3 (MVP) + 16 | MVP + imediato |
| **Fase 2 - Análise Estatística** | 7 (WDT-009 a 015) | 33 | 64 | 3-5 | High | 16 | Pós-MVP |
| **Fase 3 - Base Critérios ✅ COMPLETO (Replit)** | 4 core (WDT-016, 018, 021, 022) — 3 cancelados (WDT-017, 019, 020) | 26 | 50 | 6-10 | Critical | 17 | ✅ COMPLETO (Replit) |
| **Fase 4 - Features Avançadas** | 4 (WDT-023 a 026) | 21 | 40 | 12-14 | Medium | 18 | Pós-MVP |
| **Fase 5 - Aprendizado** | 2 (WDT-027, 028) | 21 | 38 | 15-17 | High | 18 | Pós-MVP |
| **Fase 6 - Docs & Infra** | 2 (WDT-029, 030) | 16 | 32 | 2+/18 | Medium | 19 | Transversal |
| **TOTAL** | **27** | **145** | **270** | — | — | — | — |

### Distribuição MVP vs. Pós-MVP

| Classificação | Cards | SP | % do Total |
|---------------|-------|----|------------|
| **MVP (Épico 3)** | 7 cards (WDT-001 a 007, incl. WDT-005 movido do Épico 16) → MAP-007 a MAP-013 | 23 SP | 13% |
| **Pós-MVP (Épicos 16-19)** | 20 cards (excl. 3 cancelados) | 122 SP | 84% |

---

## ARQUITETURA DO FUNIL DE TALENTOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE BUSCA WDT                         │
└─────────────────────────────────────────────────────────────────┘

  Recrutador define vaga
        │
        ▼
  ┌──────────────────┐
  │ Classificação    │  WDT-009: Alta / Média / Baixa qualificação
  │ de Vaga (LLM)    │  (Bloqueante para parametrização adaptativa)
  └────────┬─────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────┐
  │              BUSCA PARALELA                         │
  │                                                     │
  │  ┌─────────────────┐    ┌─────────────────────┐    │
  │  │  Elasticsearch   │    │   PG Vector          │    │
  │  │  (keyword+BM25)  │    │   (embeddings)       │    │
  │  │                  │    │                      │    │
  │  │  WDT-003:        │    │  WDT-004:            │    │
  │  │  exclude_ids     │    │  exclude_ids         │    │
  │  │                  │    │                      │    │
  │  │  WDT-011:        │    │  WDT-012:            │    │
  │  │  taxa de queda   │    │  gap semântico       │    │
  │  └────────┬─────────┘    └──────────┬───────────┘    │
  │           │                          │                │
  │           └──────────┬───────────────┘                │
  │                      │                                │
  │           WDT-015: Filtro pré-WRF                     │
  │           (só candidatos relevantes)                   │
  └──────────────────────┬─────────────────────────────────┘
                         │
                         ▼
              ┌────────────────────┐
              │   WRF (Weighted    │  WDT-014: K dinâmico
              │   Rank Fusion)     │  Alta: K=20-30
              │                    │  Média: K=40-50
              │                    │  Baixa: K=60-80
              └────────┬───────────┘
                       │
                       ▼
              ┌────────────────────┐
              │  WDT-001: Retorna  │  Paginação: 10 por vez
              │  10 candidatos     │  exclude_ids acumulados
              └────────┬───────────┘
                       │
                       ▼
              ┌────────────────────┐
              │  WDT-006/007:      │  Like / Dislike
              │  Feedback do       │  Fundamento de aprendizado
              │  recrutador        │
              └────────────────────┘
```

---

# ÉPICO 3: BUSCA E MAPEAMENTO — CARDS MVP (7 cards, 23 SP)

> **Timing:** Sprint 1  
> **Impacto:** Redução de ~80% no custo de tokens + fundamento para aprendizado futuro  
> **Pré-requisito:** Nenhum  
> **Complementa:** Cards MAP-001 a MAP-006 já existentes no Épico 3

---

> **⚠️ NOTA DE ATUALIZAÇÃO (07 Fev 2026):** Os 7 cards WDT deste épico (WDT-001 a WDT-004, WDT-005, WDT-006, WDT-007) foram incorporados ao documento principal `lia-mvp-cards-jira.md` como cards MAP-007 a MAP-013. Os detalhes completos com prompts IA permanecem aqui como referência técnica. O WDT-005 foi movido do Épico 16 para o Épico 3.

### CARD WDT-001: Endpoint de Busca Paginada

```yaml
Titulo: "[BE] Endpoint de busca paginada com limit 10"
Tipo: Story
Sprint: 1
Pontos: 5
Horas: 8
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search, performance

Descricao: |
  Refatorar endpoint de busca de candidatos para retornar apenas 10 
  resultados por página.
  
  Contexto: Atualmente o usuário pode solicitar 20/50/100 candidatos, 
  gerando custo excessivo de tokens e degradando WRF.
  
  Implementação:
  - Alterar controller de busca para limitar a 10 candidatos
  - Receber parâmetro 'exclude_ids' (array de IDs já retornados)
  - Passar exclude_ids para queries de Elasticsearch e PG Vector
  - Manter offset/cursor para paginação stateless
  - Remover seletor de quantidade do frontend

Historia de Usuario: |
  Como recrutador, eu quero receber 10 candidatos por vez na busca
  para ter resultados mais rápidos e relevantes, podendo carregar
  mais candidatos conforme necessidade.

Regras de Negocio:
  1. Máximo 10 candidatos por chamada de API
  2. IDs já retornados não podem aparecer em páginas subsequentes
  3. Paginação stateless via exclude_ids
  4. Performance < 2s por página
  5. Seletor de quantidade removido do frontend

Requisitos Tecnicos:
  Backend (Rails):
    - Controller: app/controllers/api/v1/searches_controller.rb
    - Parâmetros: query (string), exclude_ids (array integer), filters (hash)
    - Response: { candidates: [...], total_available: int, has_more: bool }
    - Validação: exclude_ids max 500 elementos
    - Scoping: company_id obrigatório (multi-tenant)
  Elasticsearch:
    - Query builder: app/services/search/elasticsearch_query_builder.rb
    - Adicionar must_not com ids filter
  PG Vector:
    - Query: app/services/search/pgvector_query_service.rb
    - WHERE id NOT IN (:excluded_ids)
  Testes:
    - RSpec: spec/controllers/api/v1/searches_controller_spec.rb
    - Cenários: paginação normal, com exclusão, lista vazia, max exclusões

DoD:
  - [ ] Endpoint retorna máximo 10 candidatos por chamada
  - [ ] IDs excluídos não aparecem em páginas subsequentes
  - [ ] Performance < 2s por página
  - [ ] Testes unitários cobrindo paginação e exclusão
  - [ ] Multi-tenant scoping validado

Criterios de Aceitacao:
  - [ ] GET /api/v1/searches retorna max 10 candidatos
  - [ ] Enviar exclude_ids filtra corretamente
  - [ ] has_more=false quando não há mais resultados
  - [ ] Performance não degrada com 500 IDs excluídos
  - [ ] Testes RSpec passando

Dependencias: Nenhuma
Bloqueia: WDT-002, WDT-003, WDT-004

Arquivos de Referencia (Prototipo Replit):
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - candidate-search.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/candidate-search.ts
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-001

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3 + Nuxt 3
- Banco: PostgreSQL + Elasticsearch 8.x + PG Vector (pgvector extension)
- Background Jobs: Sidekiq + Redis
- Mensageria: RabbitMQ (comunicação entre serviços)
- IA/Agentes: Python 3.11 + FastAPI + LangGraph + LangChain + Gemini 2.5 Flash
- Cache: Redis
- Testes: RSpec (Rails) + Vitest (Vue) + pytest (Python)
- API: RESTful com versionamento /api/v1/
- Autenticação: JWT via WorkOS SSO
- Multi-tenant: Scoping por company_id em todas as queries
- Referência visual: Protótipo React/Next.js/Tailwind no Replit (copiar COMPORTAMENTO, não código)

PADRÕES DE CÓDIGO:
- Rails: Service Objects para lógica de negócio, Concerns para compartilhamento, Serializers para API
- Vue: Composition API (<script setup>), composables para lógica reutilizável, Pinia para state
- Python: Classes com typing, async/await, Pydantic models
- Todos: TypeScript/tipagem estrita, sem any/untyped

---

TAREFA: Refatorar o endpoint de busca de candidatos para retornar máximo 10 resultados 
por página com suporte a exclusão de IDs já retornados.

OBJETIVO: Reduzir ~80% do custo de tokens limitando resultados a 10 por chamada.

IMPLEMENTAÇÃO NECESSÁRIA:

1. Controller (Rails):
   Arquivo: app/controllers/api/v1/searches_controller.rb
   - Aceitar parâmetro exclude_ids (array de integers)
   - Limitar resultados a 10 (constante RESULTS_PER_PAGE = 10)
   - Validar exclude_ids.length <= 500
   - Retornar { candidates: [...], total_available: int, has_more: bool }
   - Garantir scoping por current_user.company_id (multi-tenant)

2. Service Object para orquestração:
   Arquivo: app/services/search/paginated_search_service.rb
   
   class Search::PaginatedSearchService
     RESULTS_PER_PAGE = 10
     MAX_EXCLUDE_IDS = 500
     
     def initialize(query:, exclude_ids: [], filters: {}, company_id:)
       @query = query
       @exclude_ids = exclude_ids.first(MAX_EXCLUDE_IDS)
       @filters = filters
       @company_id = company_id
     end
     
     def call
       es_results = elasticsearch_search
       pgv_results = pgvector_search
       merged = wrf_merge(es_results, pgv_results)
       {
         candidates: merged.first(RESULTS_PER_PAGE),
         total_available: merged.size,
         has_more: merged.size > RESULTS_PER_PAGE
       }
     end
   end

3. Elasticsearch Query Builder:
   Arquivo: app/services/search/elasticsearch_query_builder.rb
   - Adicionar cláusula must_not com { ids: { values: exclude_ids } } no bool query
   - NÃO alterar scoring (exclusão não deve afetar relevância dos demais)
   - Testar com listas de 0, 10, 100, 500 IDs

4. PG Vector Query:
   Arquivo: app/services/search/pgvector_query_service.rb
   - Adicionar WHERE id NOT IN (:excluded_ids) na query de busca semântica
   - Garantir que distância de cossenos não é afetada
   - Usar prepared statements para performance

5. Testes RSpec:
   Arquivo: spec/services/search/paginated_search_service_spec.rb
   - Testar: retorna máximo 10, exclui IDs fornecidos, has_more correto,
     limita exclude_ids a 500, aplica scoping company_id, performance com 500 IDs

NÃO FAZER:
- NÃO criar paginação baseada em offset/page number (usar exclude_ids)
- NÃO permitir que o frontend escolha quantidade de resultados
- NÃO armazenar estado de paginação no server (stateless)
- NÃO alterar a lógica do WRF — apenas limitar o output
- NÃO esquecer multi-tenant scoping

REFERÊNCIA REPLIT:
O protótipo React/Next.js tem lista de candidatos com paginação.
Copiar o COMPORTAMENTO (paginação on-demand), mas implementar em Rails (backend).
```

---

### CARD WDT-002: Componente de Paginação On-Demand

```yaml
Titulo: "[FE] Componente de paginação on-demand"
Tipo: Story
Sprint: 1
Pontos: 3
Horas: 5
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search, ux

Descricao: |
  Criar componente Vue.js de paginação para busca de candidatos.
  
  Implementação:
  - Botão 'Carregar mais 10 candidatos' ao final da lista
  - Acumular IDs retornados no state (Pinia)
  - Enviar exclude_ids a cada nova requisição
  - Loading state durante busca
  - Indicador de 'fim dos resultados' quando retornar < 10

Historia de Usuario: |
  Como recrutador, eu quero poder carregar mais candidatos sob demanda
  para explorar o funil de forma progressiva sem sobrecarga de informação.

Regras de Negocio:
  1. Botão "Carregar mais 10 candidatos" visível ao final da lista
  2. Lista acumula candidatos (não substitui)
  3. Estado de loading durante busca
  4. Mensagem "Todos os candidatos relevantes foram exibidos" quando não há mais
  5. IDs acumulados enviados como exclude_ids

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/search/CandidateSearchResults.vue
    - Composable: src/composables/useSearchPagination.ts
    - Store (Pinia): src/stores/searchStore.ts
    - Vuetify components: v-btn, v-progress-circular, v-alert
  Integração:
    - GET /api/v1/searches?query=X&exclude_ids=[1,2,3]
  Estado:
    - searchStore.candidates: Candidate[] (acumulado)
    - searchStore.excludeIds: number[] (IDs já retornados)
    - searchStore.hasMore: boolean
    - searchStore.isLoading: boolean

DoD:
  - [ ] Botão "Carregar mais" funcional
  - [ ] Lista acumula candidatos corretamente
  - [ ] Loading state visível durante busca
  - [ ] Mensagem quando não há mais resultados
  - [ ] Testes Vitest passando

Criterios de Aceitacao:
  - [ ] Clicar "Carregar mais" adiciona 10 candidatos à lista
  - [ ] IDs acumulados corretamente em exclude_ids
  - [ ] Loading spinner durante requisição
  - [ ] Botão desaparece quando has_more=false
  - [ ] Estado preservado ao navegar e voltar

Dependencias: WDT-001
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - use-talent-funnel.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-talent-funnel.ts
```

#### Prompt para IA (Cursor/VSCode) — WDT-002

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest (Vue)
- API: RESTful com versionamento /api/v1/
- Multi-tenant: Scoping por company_id em todas as queries

PADRÕES DE CÓDIGO:
- Vue: Composition API (<script setup>), composables para lógica reutilizável, Pinia para state
- Vuetify 3: Usar componentes nativos (v-btn, v-card, v-progress-circular, etc.)
- TypeScript estrito, sem any

---

TAREFA: Criar componente Vue.js de paginação on-demand para lista de candidatos.

OBJETIVO: O recrutador vê 10 candidatos por vez e pode carregar mais sob demanda.

IMPLEMENTAÇÃO:

1. Pinia Store:
   Arquivo: src/stores/searchStore.ts
   - Estado: candidates (Candidate[], acumulado), excludeIds (number[]),
     hasMore (boolean), isLoading (boolean), query (string), filters (object)
   - Action loadMore(): chama API com exclude_ids, acumula candidatos,
     atualiza excludeIds e hasMore
   - Action resetSearch(): limpa tudo

2. Composable:
   Arquivo: src/composables/useSearchPagination.ts
   - Exporta: candidates, hasMore, isLoading, loadMore, reset
   - Usa storeToRefs para reatividade

3. Componente Vue:
   Arquivo: src/components/search/CandidateSearchResults.vue
   - v-card para cada candidato na lista
   - v-btn "Carregar mais 10 candidatos" (variant="outlined", color="primary")
     visível quando hasMore && !isLoading
   - v-progress-circular quando isLoading
   - v-alert type="info" "Todos os candidatos relevantes foram exibidos"
     quando !hasMore && candidates.length > 0

4. Testes Vitest:
   Arquivo: src/components/search/__tests__/CandidateSearchResults.spec.ts
   - Testar botão, loading, mensagem de fim, acumulação

NÃO FAZER:
- NÃO usar paginação numérica (1, 2, 3...) — usar botão "Carregar mais"
- NÃO substituir lista ao carregar — ACUMULAR
- NÃO usar React ou Tailwind — este é projeto Vue.js + Vuetify
- NÃO armazenar estado de paginação no localStorage
```

---

### CARD WDT-003: Adaptar Elasticsearch Query para Exclusão de IDs

```yaml
Titulo: "[BE] Adaptar Elasticsearch query para exclusão de IDs"
Tipo: Task
Sprint: 1
Pontos: 3
Horas: 5
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search

Descricao: |
  Modificar query builder do Elasticsearch para suportar exclusão 
  de IDs já retornados.
  
  Implementação:
  - Adicionar cláusula 'must_not' com 'ids' filter no bool query
  - Validar que exclusão não afeta scoring dos demais candidatos
  - Manter performance com listas de até 500 IDs excluídos
  - Benchmark antes/depois

Historia de Usuario: |
  Como sistema de busca, eu preciso excluir candidatos já retornados
  das queries Elasticsearch para evitar duplicatas na paginação.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/elasticsearch_query_builder.rb
    - Método: build_query(query:, filters:, exclude_ids: [])
    - Adicionar: bool > must_not > [{ ids: { values: exclude_ids } }]
    - Benchmark: rake benchmark:es_exclusion
  Testes:
    - RSpec: spec/services/search/elasticsearch_query_builder_spec.rb
    - Cenários: sem exclusão, 10 IDs, 100 IDs, 500 IDs
    - Performance: medir tempo com volumes crescentes

DoD:
  - [ ] Query com exclusão retorna resultados corretos
  - [ ] Performance não degrada com até 500 IDs
  - [ ] Scores não são afetados pela exclusão
  - [ ] Benchmark documentado

Criterios de Aceitacao:
  - [ ] Candidatos excluídos não aparecem nos resultados
  - [ ] Scores dos candidatos restantes idênticos (com e sem exclusão)
  - [ ] Performance < 2s com 500 IDs excluídos
  - [ ] Testes RSpec passando

Dependencias: WDT-001
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-003

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + Elasticsearch 8.x
- Testes: RSpec
- Gem: elasticsearch-ruby

---

TAREFA: Modificar o Elasticsearch query builder para suportar exclusão de IDs.

IMPLEMENTAÇÃO:

1. Elasticsearch Query Builder:
   Arquivo: app/services/search/elasticsearch_query_builder.rb
   
   def build_query(query:, filters: {}, exclude_ids: [], company_id:)
     bool_query = {
       must: build_must_clauses(query),
       filter: build_filter_clauses(filters, company_id)
     }
     
     if exclude_ids.present?
       bool_query[:must_not] = [
         { ids: { values: exclude_ids.map(&:to_s) } }
       ]
     end
     
     { query: { bool: bool_query }, size: 10, _source: candidate_fields }
   end

2. Pontos críticos:
   - must_not com ids filter NÃO afeta scoring dos demais (filter context)
   - Converter IDs para strings se o _id do ES é string
   - Limitar array a 500 IDs (validação no controller)

3. Benchmark rake task:
   Arquivo: lib/tasks/benchmark.rake
   - Medir tempo com 0, 10, 50, 100, 500 IDs excluídos

4. Testes RSpec:
   - Sem exclusão: retorna sem must_not
   - Com exclude_ids: adiciona must_not, não afeta scoring, aceita até 500

NÃO FAZER:
- NÃO usar must_not com term queries individuais (usar ids filter otimizado)
- NÃO colocar exclusão no must context (afetaria scoring)
- NÃO permitir arrays > 500 sem validação
```

---

### CARD WDT-004: Adaptar PG Vector Query para Exclusão de IDs

```yaml
Titulo: "[BE] Adaptar PG Vector query para exclusão de IDs"
Tipo: Task
Sprint: 1
Pontos: 2
Horas: 4
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search

Descricao: |
  Modificar query de busca semântica no PG Vector para suportar exclusão.
  
  Implementação:
  - Adicionar WHERE id NOT IN (:excluded_ids) na query pgvector
  - Validar que distância de cossenos não é afetada
  - Testar com volumes crescentes de exclusão

Historia de Usuario: |
  Como sistema de busca semântica, eu preciso excluir candidatos já retornados
  das queries PG Vector para evitar duplicatas na paginação.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/pgvector_query_service.rb
    - Query: SELECT *, embedding <=> :query_vector AS distance
             FROM candidate_embeddings
             WHERE company_id = :company_id
             AND id NOT IN (:excluded_ids)
             ORDER BY distance ASC LIMIT 10
    - Usar prepared statements / parameterized queries
  Testes:
    - RSpec: spec/services/search/pgvector_query_service_spec.rb

DoD:
  - [ ] Query com exclusão funcional
  - [ ] Distâncias semânticas corretas
  - [ ] Testes de regressão passando

Criterios de Aceitacao:
  - [ ] Candidatos excluídos não aparecem nos resultados
  - [ ] Distância de cossenos idêntica (com e sem exclusão)
  - [ ] Performance OK com 500 IDs excluídos
  - [ ] Testes RSpec passando

Dependencias: WDT-001
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - embedding_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/embedding_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-004

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + PG Vector (pgvector extension)
- Testes: RSpec
- Gem: neighbor (pgvector)

---

TAREFA: Modificar a query PG Vector para suportar exclusão de IDs já retornados.

IMPLEMENTAÇÃO:

1. PG Vector Query Service:
   Arquivo: app/services/search/pgvector_query_service.rb
   
   Opção 1 - SQL direto:
   sql = "SELECT c.*, ce.embedding <=> $1 AS distance
          FROM candidate_embeddings ce
          JOIN candidates c ON c.id = ce.candidate_id
          WHERE ce.company_id = $2
          AND ce.candidate_id NOT IN (#{exclude_ids.join(',')})
          ORDER BY distance ASC LIMIT $3"
   
   Opção 2 - ActiveRecord com neighbor gem (PREFERÍVEL):
   scope = CandidateEmbedding
     .where(company_id: company_id)
     .nearest_neighbors(:embedding, query_embedding, distance: :cosine)
     .limit(limit)
   scope = scope.where.not(candidate_id: exclude_ids) if exclude_ids.present?
   scope.includes(:candidate)

2. Validações:
   - Distância de cossenos NÃO é afetada por exclusão (verificar com testes)
   - NOT IN com arrays grandes pode ser lento — considerar NOT EXISTS se > 500
   - Usar parameterized queries (NÃO string interpolation)

NÃO FAZER:
- NÃO usar string interpolation na query (SQL injection)
- NÃO alterar a função de distância
- NÃO permitir arrays > 500 sem validação no controller
```

---

### CARD WDT-006: API de Feedback Like/Dislike

```yaml
Titulo: "[BE] API de feedback Like/Dislike para candidatos"
Tipo: Story
Sprint: 1
Pontos: 5
Horas: 8
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, feedback, learning

Descricao: |
  Criar sistema de feedback binário (like/dislike) para candidatos 
  retornados na busca.
  
  Contexto: Fundamento para todo aprendizado futuro do sistema. 
  André classificou como PRIORIDADE MUITO ALTA.
  
  Schema DB:
  - candidate_feedbacks: id, search_id, candidate_id, user_id, 
    feedback_type (like/dislike), job_id, search_query_snapshot, 
    candidate_score_snapshot, created_at
  
  Endpoints:
  - POST /api/v1/searches/:search_id/candidates/:id/feedback
  - GET /api/v1/searches/:search_id/feedbacks (listagem)
  - DELETE /api/v1/searches/:search_id/candidates/:id/feedback (remover)

Historia de Usuario: |
  Como recrutador, eu quero poder dar like ou dislike em candidatos
  retornados na busca para que o sistema aprenda minhas preferências
  e melhore os resultados futuros.

Regras de Negocio:
  1. Um feedback por candidato por busca por usuário
  2. Toggle: clicar novamente remove o feedback
  3. Snapshot do score e query salvos para análise futura
  4. Feedback vinculado à busca E à vaga
  5. Multi-tenant: feedback scoped por company_id

Requisitos Tecnicos:
  Backend (Rails):
    - Model: app/models/candidate_feedback.rb
    - Controller: app/controllers/api/v1/candidate_feedbacks_controller.rb
    - Migration: db/migrate/xxx_create_candidate_feedbacks.rb
    - Serializer: app/serializers/candidate_feedback_serializer.rb
    - Validações: uniqueness [search_id, candidate_id, user_id]
  Schema:
    - candidate_feedbacks:
      - id (bigint PK)
      - search_id (bigint FK)
      - candidate_id (bigint FK)
      - user_id (bigint FK)
      - job_id (bigint FK)
      - company_id (bigint FK)
      - feedback_type (enum: like/dislike)
      - search_query_snapshot (jsonb)
      - candidate_score_snapshot (jsonb)
      - created_at, updated_at
    - Índices: [search_id, candidate_id, user_id] unique, [company_id], [job_id]

DoD:
  - [ ] Migration criada e executada
  - [ ] Endpoints funcionais com validações
  - [ ] Um feedback por candidato por busca por usuário
  - [ ] Snapshot do score e query salvos
  - [ ] Testes de integração

Criterios de Aceitacao:
  - [ ] POST cria feedback com tipo like ou dislike
  - [ ] POST com mesmo candidato/busca/user atualiza existente
  - [ ] DELETE remove feedback
  - [ ] GET lista todos feedbacks de uma busca
  - [ ] Snapshots salvos corretamente em JSONB
  - [ ] Validação de unicidade funcional
  - [ ] Multi-tenant scoping por company_id

Dependencias: Nenhuma
Bloqueia: WDT-007, WDT-008, WDT-027, WDT-028

Arquivos de Referencia (Prototipo Replit):
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - feedback_learning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feedback_learning_service.py
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/search/calibration/feedback/route.ts
```

#### Prompt para IA (Cursor/VSCode) — WDT-006

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL
- Testes: RSpec
- API: RESTful /api/v1/
- Multi-tenant: Scoping por company_id

---

TAREFA: Criar sistema de feedback binário (like/dislike) para candidatos.
Este é o FUNDAMENTO para todo aprendizado futuro do sistema.

IMPLEMENTAÇÃO:

1. Migration:
   class CreateCandidateFeedbacks < ActiveRecord::Migration[7.1]
     def change
       create_table :candidate_feedbacks do |t|
         t.references :search, null: false, foreign_key: true
         t.references :candidate, null: false, foreign_key: true
         t.references :user, null: false, foreign_key: true
         t.references :job, null: false, foreign_key: true
         t.references :company, null: false, foreign_key: true
         t.integer :feedback_type, null: false
         t.jsonb :search_query_snapshot, default: {}
         t.jsonb :candidate_score_snapshot, default: {}
         t.timestamps
       end
       add_index :candidate_feedbacks,
         [:search_id, :candidate_id, :user_id],
         unique: true, name: 'idx_feedback_unique_per_search'
     end
   end

2. Model:
   class CandidateFeedback < ApplicationRecord
     belongs_to :search
     belongs_to :candidate
     belongs_to :user
     belongs_to :job
     belongs_to :company
     enum feedback_type: { like: 0, dislike: 1 }
     validates :feedback_type, presence: true
     validates :candidate_id, uniqueness: {
       scope: [:search_id, :user_id],
       message: "já possui feedback nesta busca"
     }
     before_create :capture_snapshots
     scope :for_company, ->(company_id) { where(company_id: company_id) }
     scope :likes, -> { where(feedback_type: :like) }
     scope :dislikes, -> { where(feedback_type: :dislike) }
   end

3. Controller:
   module Api::V1
     class CandidateFeedbacksController < BaseController
       before_action :set_search
       def create
         feedback = @search.candidate_feedbacks.find_or_initialize_by(
           candidate_id: params[:candidate_id], user_id: current_user.id
         )
         feedback.assign_attributes(feedback_params)
         feedback.company_id = current_user.company_id
         feedback.job_id = @search.job_id
         if feedback.save
           render json: CandidateFeedbackSerializer.new(feedback), status: :ok
         else
           render json: { errors: feedback.errors.full_messages }, status: :unprocessable_entity
         end
       end
       def index
         feedbacks = @search.candidate_feedbacks.where(company_id: current_user.company_id)
         render json: CandidateFeedbackSerializer.new(feedbacks)
       end
       def destroy
         feedback = @search.candidate_feedbacks.find_by!(
           candidate_id: params[:candidate_id], user_id: current_user.id
         )
         feedback.destroy!
         head :no_content
       end
     end
   end

4. Routes:
   namespace :api do
     namespace :v1 do
       resources :searches do
         resources :candidate_feedbacks, only: [:create, :index, :destroy],
           path: 'candidates/:candidate_id/feedback'
       end
     end
   end

5. Testes RSpec:
   Testar: criação, unicidade, toggle, snapshots, multi-tenant scoping, listagem, remoção.

IMPORTÂNCIA: Os snapshots de query e score são essenciais para análise retroativa
no motor de aprendizado futuro (WDT-027, WDT-028).

NÃO FAZER:
- NÃO permitir feedback sem search_id
- NÃO esquecer os snapshots (dados históricos irrecuperáveis)
- NÃO expor feedbacks entre companies (multi-tenant)
```

---

### CARD WDT-007: Componente Like/Dislike no Card de Candidato

```yaml
Titulo: "[FE] Componente Like/Dislike no card de candidato"
Tipo: Story
Sprint: 1
Pontos: 3
Horas: 5
Prioridade: Alta
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, feedback, ux

Descricao: |
  Adicionar botões de like/dislike em cada card de candidato 
  na lista de resultados.
  
  Implementação:
  - Ícones de thumbs up/down no card
  - Toggle (clique novamente para remover)
  - Feedback visual imediato (cor/destaque)
  - Persistir via API
  - Estado sincronizado entre páginas

Historia de Usuario: |
  Como recrutador, eu quero poder dar like ou dislike rapidamente
  em cada candidato para registrar minha avaliação inicial
  e ajudar o sistema a aprender.

Regras de Negocio:
  1. Botões visíveis em cada card de candidato
  2. Feedback persiste ao navegar entre páginas
  3. Toggle funcional (clicar novamente remove)
  4. Loading state durante save
  5. Feedback visual imediato (optimistic update)

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/search/CandidateFeedbackButtons.vue
    - Composable: src/composables/useCandidateFeedback.ts
    - API: src/api/feedbackApi.ts
    - Vuetify: v-btn com v-icon (mdi-thumb-up, mdi-thumb-down)
    - Cores: like = success (green), dislike = error (red), inativo = grey
  Integração:
    - POST /api/v1/searches/:search_id/candidates/:id/feedback
    - DELETE /api/v1/searches/:search_id/candidates/:id/feedback

DoD:
  - [ ] Botões visíveis e funcionais
  - [ ] Feedback persiste ao navegar
  - [ ] Toggle funcional
  - [ ] Loading state durante save
  - [ ] Testes Vitest passando

Criterios de Aceitacao:
  - [ ] Ícones thumbs up/down visíveis em cada card
  - [ ] Clicar em like ativa (verde) e persiste via API
  - [ ] Clicar em dislike ativa (vermelho) e persiste via API
  - [ ] Clicar novamente no mesmo botão remove feedback
  - [ ] Estado sincronizado ao carregar mais candidatos

Dependencias: WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - message-feedback.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/chat/message-feedback.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/search/calibration/feedback/route.ts
```

#### Prompt para IA (Cursor/VSCode) — WDT-007

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest
- API: RESTful /api/v1/

---

TAREFA: Criar componente Vue.js de Like/Dislike para o card de candidato.

IMPLEMENTAÇÃO:

1. API Service:
   Arquivo: src/api/feedbackApi.ts
   - create(searchId, candidateId, { feedback_type: 'like' | 'dislike' })
   - remove(searchId, candidateId)
   - list(searchId)

2. Composable:
   Arquivo: src/composables/useCandidateFeedback.ts
   - Exporta: currentFeedback (ref), isLoading (ref), toggleFeedback (fn)
   - toggleFeedback('like'|'dislike'): se já ativo, remove; se diferente, atualiza

3. Componente Vue:
   Arquivo: src/components/search/CandidateFeedbackButtons.vue
   - v-btn icon size="small" para like (mdi-thumb-up)
     color="success" quando ativo, "grey" quando inativo
     variant="flat" quando ativo, "text" quando inativo
   - v-btn icon size="small" para dislike (mdi-thumb-down)
     color="error" quando ativo, "grey" quando inativo
   - Props: searchId (number), candidateId (number), initialFeedback (string|null)

4. Testes Vitest:
   - Testar toggle, loading, estado visual, persistência

DESIGN:
- Usar ícones Material Design (mdi-thumb-up, mdi-thumb-down) do Vuetify
- Like ativo: variant="flat" color="success"
- Dislike ativo: variant="flat" color="error"
- Inativo: variant="text" color="grey"
- Optimistic update: mudar cor imediatamente, reverter se API falhar

NÃO FAZER:
- NÃO usar React ou Tailwind
- NÃO usar ícones de terceiros (usar mdi do Vuetify)
- NÃO implementar campo de comentário (será card futuro)
```

---

# ÉPICO 16: OTIMIZAÇÃO ESTATÍSTICA DE BUSCA (8 cards, 38 SP)

> **Timing:** Pós-MVP, Sprints 2-5  
> **Impacto:** Parametrização adaptativa, WRF inteligente, redução de ruído nos resultados  
> **Pré-requisito:** Épico 3 MVP completo  
> **Bloqueante para:** Épico 17 (Base de Critérios depende de classificação WDT-009)  
> **Nota:** WDT-005 (Remover ordenação por ranking) foi movido para o Épico 3 como MAP-013.

---

### CARD WDT-005: Remover Ordenação Automática por Ranking

```yaml
Titulo: "[FE] Remover ordenação automática por ranking"
Tipo: Story
Sprint: 2
Pontos: 2
Horas: 3
Prioridade: Alta
Epic: EPIC-3 (Busca e Mapeamento) — movido do Épico 16
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, ux, ethics

Descricao: |
  Remover a ordenação automática de candidatos por score na interface.
  
  Contexto: Ranking ordenado cria expectativa de que o primeiro é sempre 
  melhor, gerando questionamentos sobre viés comercial (candidatos pagantes) 
  e removendo autonomia do recrutador.
  
  Implementação:
  - Exibir candidatos na ordem retornada pela API (sem sort no front)
  - Manter scores visíveis em cada card de candidato
  - Adicionar botão/dropdown 'Ordenar por: Score / Nome / Data'
  - Default: sem ordenação (ordem de retorno)

Historia de Usuario: |
  Como recrutador, eu quero ver candidatos relevantes sem hierarquia
  rígida de ranking para poder avaliar com autonomia e sem viés.

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/search/SearchSortDropdown.vue
    - Vuetify: v-select com opções de ordenação
    - Opções: "Relevância (padrão)" | "Score (maior)" | "Nome A-Z" | "Data"
    - Default: ordem de retorno da API
    - Tooltip: "Candidatos relevantes para sua busca"
  Dados:
    - Scores continuam visíveis nos cards (badge ou chip)
    - Ordenação acontece apenas no frontend (não refaz busca)

DoD:
  - [ ] Candidatos não são ordenados por score por padrão
  - [ ] Scores visíveis mas não hierarquizados
  - [ ] Opção de ordenação manual disponível
  - [ ] Tooltip informativo

Criterios de Aceitacao:
  - [ ] Lista exibe candidatos na ordem da API por padrão
  - [ ] Dropdown de ordenação funcional
  - [ ] Tooltip explica que são "candidatos relevantes"
  - [ ] Score visível em cada card sem criar hierarquia

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - useUnifiedSearch.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useUnifiedSearch.ts
```

#### Prompt para IA (Cursor/VSCode) — WDT-005

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest

---

TAREFA: Remover ordenação automática por score e adicionar dropdown de ordenação manual.

OBJETIVO: Evitar viés comercial e devolver autonomia ao recrutador.

IMPLEMENTAÇÃO:

1. Componente SearchSortDropdown.vue:
   - v-select com items: [
       { title: 'Relevância (padrão)', value: 'default' },
       { title: 'Score (maior primeiro)', value: 'score_desc' },
       { title: 'Nome A-Z', value: 'name_asc' },
       { title: 'Data de cadastro', value: 'date_desc' }
     ]
   - Default: 'default' (ordem da API)
   - Emit 'update:sortBy' para componente pai

2. Ordenação no frontend:
   - computed sortedCandidates que aplica sort local (sem nova requisição)
   - 'default': mantém ordem da API (sem sort)
   - 'score_desc': sort por score decrescente
   - 'name_asc': sort por nome alfabético
   - 'date_desc': sort por data mais recente

3. Tooltip no header:
   - v-tooltip no título da lista: "Estes são candidatos relevantes 
     para sua busca. Use o filtro de ordenação se preferir uma ordem específica."

NÃO FAZER:
- NÃO remover scores dos cards (devem continuar visíveis)
- NÃO reordenar automaticamente por score
- NÃO chamar API ao mudar ordenação (sort é local)
```

---

### CARD WDT-008: Dashboard Básico de Métricas de Feedback

```yaml
Titulo: "[BE/FE] Dashboard básico de métricas de feedback"
Tipo: Story
Sprint: 2
Pontos: 5
Horas: 8
Prioridade: Média
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: feedback, analytics, dashboard

Descricao: |
  Dashboard simples para visualizar padrões de feedback dos recrutadores.
  
  Métricas:
  - Total likes vs dislikes por período
  - Taxa de like por faixa de score (o score X-Y tem %N de likes?)
  - Top motivos de dislike (se campo de comentário existir)
  - Feedback por tipo de vaga
  - Feedback por recrutador

Historia de Usuario: |
  Como admin, eu quero visualizar padrões de feedback dos recrutadores
  para entender se os resultados da busca estão satisfatórios.

Requisitos Tecnicos:
  Backend (Rails):
    - Controller: app/controllers/api/v1/admin/feedback_analytics_controller.rb
    - Service: app/services/analytics/feedback_analytics_service.rb
    - Queries agregadas em CandidateFeedback
    - Cache Redis com TTL 5 min para queries pesadas
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/FeedbackDashboard.vue
    - Componentes: gráficos com Chart.js ou ApexCharts
    - Vuetify: v-card, v-data-table, v-chip para métricas

DoD:
  - [ ] Dashboard acessível para admins
  - [ ] Gráficos de like/dislike ratio
  - [ ] Filtros por período e tipo de vaga
  - [ ] Dados atualizados (cache 5 min)

Criterios de Aceitacao:
  - [ ] Total likes vs dislikes exibido
  - [ ] Taxa de like por faixa de score calculada
  - [ ] Filtros por período funcionais
  - [ ] Apenas admins acessam

Dependencias: WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - strategic-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/strategic-dashboard.tsx
  - chart-components.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/charts/chart-components.tsx
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-008

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3 + Nuxt 3
- Cache: Redis
- Testes: RSpec + Vitest

---

TAREFA: Criar dashboard de métricas de feedback (like/dislike) para admins.

IMPLEMENTAÇÃO:

Backend (Rails):
1. Service: app/services/analytics/feedback_analytics_service.rb
   - total_by_type(period:): COUNT group by feedback_type
   - like_rate_by_score_range: agrupa feedbacks por faixa de score (0-25, 25-50, etc.)
   - feedback_by_job_type: agrupa por qualification_level da vaga
   - feedback_by_recruiter: agrupa por user_id
   - Cachear com Redis.cache(key, expires_in: 5.minutes)

2. Controller: app/controllers/api/v1/admin/feedback_analytics_controller.rb
   - GET /api/v1/admin/feedback-analytics
   - Parâmetros: period (7d, 30d, 90d), job_type (optional)
   - Autorização: apenas role=admin

Frontend (Vue.js):
1. Página: src/pages/admin/FeedbackDashboard.vue
   - Usar ApexCharts (vue3-apexcharts) para gráficos
   - Gráfico de donut: likes vs dislikes
   - Gráfico de barras: like rate por faixa de score
   - v-data-table: feedback por recrutador
   - v-select para filtro de período

NÃO FAZER:
- NÃO expor dados entre companies (multi-tenant)
- NÃO calcular em real-time sem cache (usar Redis)
```

---

### CARD WDT-009: Classificação Automática de Nível de Qualificação da Vaga

```yaml
Titulo: "[BE] Classificação automática de nível de qualificação da vaga"
Tipo: Story
Sprint: 3
Pontos: 8
Horas: 16
Prioridade: Crítica
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, classification, blocker

Descricao: |
  Criar sistema de classificação automática do nível de qualificação 
  de vagas usando LLM.
  
  Contexto: André identificou que critérios para CEO são completamente 
  diferentes de atendente de loja. Esta classificação é BLOQUEANTE para 
  toda parametrização adaptativa (WDT-011, WDT-012, WDT-014).
  
  Implementação:
  - Prompt LLM (Gemini) para analisar descrição da vaga
  - Classificar em: Alta (Executive Search), Média (Especialista), Baixa (Operacional)
  - Salvar classificação no modelo Job (campo qualification_level)
  - Override manual possível pelo recrutador

Historia de Usuario: |
  Como sistema, eu preciso classificar automaticamente o nível de
  qualificação da vaga para adaptar os parâmetros de busca e avaliação.

Regras de Negocio:
  1. Classificação automática ao criar/editar vaga
  2. 3 níveis: alta (executive search), média (especialista), baixa (operacional)
  3. Campo salvo no banco (qualification_level)
  4. Override manual possível pelo recrutador
  5. Classificação afeta K do WRF e thresholds de filtragem

Requisitos Tecnicos:
  Backend (Rails + Python):
    - Migration: adicionar qualification_level (enum) na tabela jobs
    - Rails Service: app/services/jobs/qualification_classifier_service.rb
    - Chamada para Python FastAPI: POST /api/v1/ai/classify-job-level
    - Callback after_save no modelo Job para classificar
  Python (FastAPI):
    - Endpoint: POST /api/v1/ai/classify-job-level
    - Prompt Gemini para classificação
    - Response: { level: "alta"|"media"|"baixa", confidence: float, reasoning: string }
  Testes:
    - RSpec: spec/services/jobs/qualification_classifier_service_spec.rb
    - pytest: tests/test_classify_job_level.py
    - Testar com 20+ vagas de tipos diferentes

DoD:
  - [ ] Classificação automática ao criar/editar vaga
  - [ ] 3 níveis funcionais: alta/média/baixa
  - [ ] Campo salvo no banco
  - [ ] Override manual possível
  - [ ] Testes com 20+ vagas de diferentes tipos
  - [ ] Prompt documentado e versionado

Criterios de Aceitacao:
  - [ ] Vaga de CEO classificada como "alta"
  - [ ] Vaga de desenvolvedor sênior classificada como "média"
  - [ ] Vaga de atendente classificada como "baixa"
  - [ ] Recrutador pode alterar classificação manualmente
  - [ ] Classificação persiste no banco
  - [ ] Testes passando

Dependencias: Nenhuma
Bloqueia: WDT-010, WDT-011, WDT-012, WDT-014

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - job_context_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_context_service.py
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-009

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Python 3.11 + FastAPI
- Banco: PostgreSQL
- IA: Gemini 2.5 Flash via LangChain
- Testes: RSpec + pytest

---

TAREFA: Criar classificação automática de nível de qualificação da vaga usando LLM.
ESTE CARD É BLOQUEANTE para toda parametrização adaptativa.

IMPLEMENTAÇÃO:

1. Migration (Rails):
   add_column :jobs, :qualification_level, :integer, default: 1
   # enum: { baixa: 0, media: 1, alta: 2 }
   add_column :jobs, :qualification_confidence, :float
   add_column :jobs, :qualification_reasoning, :text
   add_column :jobs, :qualification_override, :boolean, default: false

2. Model Job (Rails):
   enum qualification_level: { baixa: 0, media: 1, alta: 2 }
   after_save :classify_qualification, if: :saved_change_to_description?

3. Service (Rails):
   app/services/jobs/qualification_classifier_service.rb
   - Chama Python FastAPI: POST /api/v1/ai/classify-job-level
   - Body: { title, description, requirements, salary_range }
   - Salva resultado no Job
   - Não sobrescreve se qualification_override=true

4. Endpoint Python (FastAPI):
   app/routers/ai/classification.py
   
   Prompt Gemini:
   "Analise esta vaga e classifique o nível de qualificação:
   - ALTA: Cargos de diretoria, C-level, VP, posições de executive search
   - MEDIA: Especialistas, seniores, coordenadores, gerentes de área
   - BAIXA: Operacionais, júnior, assistentes, atendimento
   
   Vaga: {title}
   Descrição: {description}
   Requisitos: {requirements}
   Faixa salarial: {salary_range}
   
   Responda em JSON: { level: 'alta'|'media'|'baixa', confidence: 0-1, reasoning: 'texto' }"

5. Testes:
   - Testar com vagas CEO, Dev Sênior, Atendente
   - Verificar que override manual não é sobrescrito
   - Testar callback after_save

NÃO FAZER:
- NÃO hardcodar classificação
- NÃO ignorar salary_range na classificação (é forte indicador)
- NÃO sobrescrever override manual do recrutador
```

---

### CARD WDT-010: Exibição e Override da Classificação de Vaga

```yaml
Titulo: "[FE] Exibição e override da classificação de vaga"
Tipo: Task
Sprint: 3
Pontos: 2
Horas: 4
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: ux, classification

Descricao: |
  Exibir a classificação automática na interface de edição de vaga 
  e permitir override manual.
  - Badge visual (Alta/Média/Baixa) na vaga
  - Dropdown para override manual
  - Tooltip explicando impacto na busca

Historia de Usuario: |
  Como recrutador, eu quero ver a classificação da minha vaga e poder
  ajustá-la se discordar da classificação automática.

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/jobs/QualificationBadge.vue
    - v-chip com cores: alta=purple, média=blue, baixa=green
    - v-select para override
    - v-tooltip explicando impacto

DoD:
  - [ ] Badge visível na vaga
  - [ ] Override funcional
  - [ ] Tooltip informativo

Criterios de Aceitacao:
  - [ ] Badge com cor correta por nível
  - [ ] Override altera classificação via API
  - [ ] Tooltip explica impacto na busca

Dependencias: WDT-009
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - advanced-search.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/advanced-search.tsx
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-010

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3

---

TAREFA: Exibir classificação de vaga com badge visual e permitir override.

IMPLEMENTAÇÃO:
1. Componente QualificationBadge.vue:
   - v-chip com cores por nível:
     alta: color="deep-purple" icon="mdi-crown"
     média: color="blue" icon="mdi-briefcase"
     baixa: color="green" icon="mdi-account-hard-hat"
   - v-tooltip: "Esta vaga foi classificada como [nível]. Isso afeta a 
     precisão da busca e critérios de avaliação."
   - v-select inline para override (se admin/recrutador)

2. Props: qualificationLevel, canOverride, confidence
3. Emit: 'update:level' com PATCH para API

NÃO FAZER:
- NÃO usar cores do accent LIA (cyan) — usar cores semânticas
```

---

### CARD WDT-011: Cálculo de Taxa de Queda de Score (Elasticsearch)

```yaml
Titulo: "[BE] Cálculo de taxa de queda de score (Elasticsearch)"
Tipo: Story
Sprint: 4
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, statistics, optimization

Descricao: |
  Implementar análise estatística de taxa de queda de score nos resultados
  do Elasticsearch.
  
  Contexto: André propôs identificar o 'cotovelo' onde scores começam a 
  achatar para filtrar candidatos irrelevantes ANTES do WRF.
  
  Fórmula: queda_percentual = ((score_melhor - score_pior) / score_melhor) * 100
  
  Implementação:
  - Calcular queda percentual entre top score e cada candidato
  - Identificar ponto de inflexão (cotovelo) na curva
  - Threshold dinâmico baseado em qualification_level da vaga
  - Filtrar candidatos abaixo do threshold antes do WRF
  - Logar análise para observabilidade

Historia de Usuario: |
  Como sistema de busca, eu preciso identificar automaticamente onde os
  scores do Elasticsearch deixam de ser significativos para filtrar
  candidatos irrelevantes antes do WRF.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/es_score_drop_analyzer.rb
    - Recebe: array de resultados ES com scores
    - Calcula: queda percentual entre cada candidato e o top
    - Identifica: ponto de inflexão (cotovelo)
    - Thresholds por qualification_level:
      - Alta: queda > 40% = corte
      - Média: queda > 55% = corte
      - Baixa: queda > 70% = corte
    - Output: candidatos filtrados + log de análise
  Testes:
    - RSpec: spec/services/search/es_score_drop_analyzer_spec.rb

DoD:
  - [ ] Cálculo implementado e testado
  - [ ] Threshold adaptativo por tipo de vaga
  - [ ] Log de análise salvo
  - [ ] Candidatos abaixo do threshold filtrados
  - [ ] Métricas: % de candidatos filtrados por busca

Criterios de Aceitacao:
  - [ ] Ponto de inflexão identificado corretamente
  - [ ] Thresholds aplicados por qualification_level
  - [ ] Log registra: total candidatos, ponto de corte, % filtrados
  - [ ] Testes com datasets variados passando

Dependencias: WDT-009
Bloqueia: WDT-015

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-011

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: Elasticsearch 8.x
- Testes: RSpec

---

TAREFA: Implementar análise de taxa de queda de score nos resultados Elasticsearch
para filtrar candidatos irrelevantes ANTES do WRF.

IMPLEMENTAÇÃO:

1. Service:
   Arquivo: app/services/search/es_score_drop_analyzer.rb

   class Search::EsScoreDropAnalyzer
     THRESHOLDS = {
       alta:  0.40,  # corte quando queda > 40%
       media: 0.55,  # corte quando queda > 55%
       baixa: 0.70   # corte quando queda > 70%
     }.freeze

     def initialize(results:, qualification_level:)
       @results = results.sort_by { |r| -r[:score] }
       @level = qualification_level.to_sym
       @threshold = THRESHOLDS[@level]
     end

     def analyze
       return @results if @results.size <= 1
       top_score = @results.first[:score]
       cutoff_index = find_cutoff(top_score)
       filtered = @results.first(cutoff_index)
       log_analysis(top_score, cutoff_index)
       filtered
     end

     private

     def find_cutoff(top_score)
       @results.each_with_index do |result, idx|
         drop = (top_score - result[:score]) / top_score.to_f
         return idx if drop > @threshold
       end
       @results.size
     end

     def log_analysis(top_score, cutoff_index)
       Rails.logger.info("[EsScoreDropAnalyzer] level=#{@level} " \
         "total=#{@results.size} cutoff_at=#{cutoff_index} " \
         "filtered=#{@results.size - cutoff_index} " \
         "top_score=#{top_score}")
     end
   end

2. Configurar thresholds como variáveis de ambiente para ajuste sem deploy:
   ES_SCORE_DROP_THRESHOLD_ALTA=0.40
   ES_SCORE_DROP_THRESHOLD_MEDIA=0.55
   ES_SCORE_DROP_THRESHOLD_BAIXA=0.70

3. Testes com datasets variados:
   - Queda gradual (muitos candidatos relevantes)
   - Queda abrupta (poucos relevantes)
   - Todos com score similar (sem corte)
   - Um único candidato relevante (corte em 1)

NÃO FAZER:
- NÃO hardcodar thresholds sem fallback para env vars
- NÃO aplicar corte se resultado tem < 3 candidatos
```

---

### CARD WDT-012: Cálculo de Gap Semântico (PG Vector)

```yaml
Titulo: "[BE] Cálculo de gap semântico (PG Vector)"
Tipo: Story
Sprint: 4
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, statistics, optimization

Descricao: |
  Implementar análise de gap semântico nos resultados do PG Vector.
  
  Contexto: Similar à taxa de queda do ES, mas para distância de cossenos.
  
  Implementação:
  - Calcular diferença de distância entre candidatos consecutivos
  - Identificar 'salto' na distância (gap significativo)
  - Threshold dinâmico baseado em qualification_level
  - Filtrar candidatos após o gap antes de enviar para WRF
  - Análise de desvio padrão complementar

Historia de Usuario: |
  Como sistema de busca, eu preciso identificar onde a distância
  semântica dá um "salto" significativo para filtrar candidatos
  irrelevantes do PG Vector antes do WRF.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/pgv_gap_analyzer.rb
    - Recebe: array de resultados PGV com distâncias
    - Calcula: diferença de distância entre candidatos consecutivos
    - Identifica: gap > N * desvio padrão
    - Threshold adaptativo por qualification_level
    - Output: candidatos filtrados + log de análise
  Testes:
    - RSpec: spec/services/search/pgv_gap_analyzer_spec.rb

DoD:
  - [ ] Gap calculado corretamente
  - [ ] Threshold adaptativo funcional
  - [ ] Filtro pré-WRF implementado
  - [ ] Logs de análise salvos

Criterios de Aceitacao:
  - [ ] Gap identificado entre candidatos consecutivos
  - [ ] Threshold aplicado por qualification_level
  - [ ] Candidatos após gap removidos
  - [ ] Log com métricas de filtragem

Dependencias: WDT-009
Bloqueia: WDT-015

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - embedding_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/embedding_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-012

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + PG Vector
- Testes: RSpec

---

TAREFA: Implementar análise de gap semântico nos resultados PG Vector.

IMPLEMENTAÇÃO:

1. Service:
   Arquivo: app/services/search/pgv_gap_analyzer.rb

   class Search::PgvGapAnalyzer
     GAP_MULTIPLIERS = {
       alta:  1.5,  # gap > 1.5x desvio padrão = corte
       media: 2.0,
       baixa: 2.5
     }.freeze

     def initialize(results:, qualification_level:)
       @results = results.sort_by { |r| r[:distance] }
       @level = qualification_level.to_sym
       @multiplier = GAP_MULTIPLIERS[@level]
     end

     def analyze
       return @results if @results.size <= 2
       gaps = calculate_consecutive_gaps
       std_dev = standard_deviation(gaps)
       mean_gap = gaps.sum / gaps.size.to_f
       cutoff = find_gap_cutoff(gaps, mean_gap, std_dev)
       @results.first(cutoff + 1)
     end

     private

     def calculate_consecutive_gaps
       @results.each_cons(2).map { |a, b| b[:distance] - a[:distance] }
     end

     def find_gap_cutoff(gaps, mean, std_dev)
       threshold = mean + (@multiplier * std_dev)
       gaps.each_with_index do |gap, idx|
         return idx if gap > threshold
       end
       @results.size - 1
     end
   end

NÃO FAZER:
- NÃO confundir distância (menor=melhor) com score (maior=melhor)
- NÃO aplicar corte se < 3 candidatos
```

---

### CARD WDT-013: Teste de Estabilidade Intra-Query

```yaml
Titulo: "[BE] Teste de estabilidade intra-query (dev/staging)"
Tipo: Story
Sprint: 4
Pontos: 3
Horas: 6
Prioridade: Média
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, quality, diagnostics

Descricao: |
  Criar ferramenta de diagnóstico que executa mesma query múltiplas 
  vezes e verifica consistência.
  
  Contexto: André alertou que se rankings mudam significativamente 
  entre execuções idênticas, a parametrização precisa de ajuste.

Historia de Usuario: |
  Como desenvolvedor, eu quero testar se a mesma busca retorna resultados
  consistentes para garantir estabilidade do sistema.

Requisitos Tecnicos:
  Backend (Rails):
    - Rake task: lib/tasks/search_stability.rake
    - Endpoint admin: GET /api/v1/admin/search-stability?query=X&runs=5
    - Executa query N vezes (3-5x)
    - Compara IDs e posições retornadas
    - Calcula índice de estabilidade (% candidatos que mantêm posição)
    - Alerta se divergência > threshold configurável

DoD:
  - [ ] Task executável via CLI ou admin
  - [ ] Relatório de estabilidade gerado
  - [ ] Alerta em caso de instabilidade
  - [ ] Resultados comparados por fonte (ES vs PGV)

Criterios de Aceitacao:
  - [ ] Rake task funcional: rails search:stability_test[query,5]
  - [ ] Relatório com % de estabilidade
  - [ ] Comparação ES vs PGV separada
  - [ ] Alerta quando estabilidade < 80%

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-013

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: Elasticsearch + PG Vector

---

TAREFA: Criar ferramenta de diagnóstico de estabilidade de queries.

IMPLEMENTAÇÃO:

1. Rake task:
   lib/tasks/search_stability.rake
   
   namespace :search do
     desc "Test search query stability"
     task :stability_test, [:query, :runs] => :environment do |t, args|
       query = args[:query]
       runs = (args[:runs] || 5).to_i
       
       es_results = runs.times.map { elasticsearch_search(query) }
       pgv_results = runs.times.map { pgvector_search(query) }
       
       es_stability = calculate_stability(es_results)
       pgv_stability = calculate_stability(pgv_results)
       
       puts "ES Stability: #{es_stability}%"
       puts "PGV Stability: #{pgv_stability}%"
       puts "WARNING: Unstable!" if es_stability < 80 || pgv_stability < 80
     end
   end

2. calculate_stability: compara IDs retornados em cada run
   - % de IDs que aparecem em TODAS as runs
   - Variação de posição média por candidato

NÃO FAZER:
- NÃO rodar em produção automaticamente (apenas dev/staging)
- NÃO expor endpoint para usuários comuns (admin only)
```

---

### CARD WDT-014: Parametrização Dinâmica do K no WRF

```yaml
Titulo: "[BE] Parametrização dinâmica do K no WRF"
Tipo: Story
Sprint: 5
Pontos: 5
Horas: 8
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, wrf, optimization

Descricao: |
  Tornar o parâmetro K do Weighted Rank Fusion dinâmico baseado no tipo de vaga.
  
  Contexto: K padrão é 60. André explicou: K menor = mais criterioso, 
  K maior = menos criterioso.
  
  Implementação:
  - Alta qualificação: K=20-30 (mais criterioso)
  - Média qualificação: K=40-50
  - Baixa qualificação: K=60-80 (menos criterioso)
  - Usar qualification_level da vaga para selecionar K
  - Valores configuráveis via settings/env (não hardcoded)
  - Logar K utilizado em cada busca

Historia de Usuario: |
  Como sistema de busca, eu preciso ajustar automaticamente a
  sensibilidade do WRF com base na complexidade da vaga.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/wrf_service.rb (modificar)
    - Receber qualification_level e selecionar K
    - Valores via ENV: WRF_K_ALTA=25, WRF_K_MEDIA=45, WRF_K_BAIXA=70
    - Log do K utilizado em cada busca
  Testes:
    - RSpec: comparar resultados com K fixo vs dinâmico

DoD:
  - [ ] K dinâmico implementado
  - [ ] Valores configuráveis externamente
  - [ ] Log do K por busca
  - [ ] Testes comparando K fixo vs dinâmico

Criterios de Aceitacao:
  - [ ] Vaga alta usa K=20-30
  - [ ] Vaga média usa K=40-50
  - [ ] Vaga baixa usa K=60-80
  - [ ] K logado em cada busca
  - [ ] Valores ajustáveis via ENV

Dependencias: WDT-009
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-014

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + Elasticsearch + PG Vector

---

TAREFA: Tornar o K do Weighted Rank Fusion dinâmico por tipo de vaga.

IMPLEMENTAÇÃO:

1. Modificar WRF Service:
   app/services/search/wrf_service.rb

   K_VALUES = {
     alta:  ENV.fetch('WRF_K_ALTA', 25).to_i,
     media: ENV.fetch('WRF_K_MEDIA', 45).to_i,
     baixa: ENV.fetch('WRF_K_BAIXA', 70).to_i
   }.freeze

   def merge(es_results, pgv_results, qualification_level:)
     k = K_VALUES[qualification_level.to_sym]
     Rails.logger.info("[WRF] K=#{k} for level=#{qualification_level}")
     
     # WRF formula: score = sum(1 / (k + rank_i))
     merged_scores = {}
     [es_results, pgv_results].each do |results|
       results.each_with_index do |candidate, rank|
         id = candidate[:id]
         merged_scores[id] ||= 0
         merged_scores[id] += 1.0 / (k + rank + 1)
       end
     end
     merged_scores.sort_by { |_, score| -score }.map(&:first)
   end

NÃO FAZER:
- NÃO hardcodar K sem fallback para ENV
- NÃO alterar a fórmula WRF (apenas o K)
```

---

### CARD WDT-015: Filtro Pré-WRF Combinando Análises Estatísticas

```yaml
Titulo: "[BE] Filtro pré-WRF combinando análises estatísticas"
Tipo: Story
Sprint: 5
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, wrf, performance

Descricao: |
  Orquestrar filtros estatísticos (taxa de queda + gap semântico) antes do WRF.
  
  Contexto: André propôs não passar automaticamente 100 de cada fonte. 
  Passar apenas os relevantes.
  
  Pipeline:
  - ES results → taxa de queda → candidatos filtrados ES
  - PGV results → gap semântico → candidatos filtrados PGV
  - Merge: candidatos filtrados ES + PGV → WRF
  - Exemplo: Se saíram 20 do ES e 40 do PGV, WRF recebe 60 (não 200)

Historia de Usuario: |
  Como sistema de busca, eu preciso filtrar candidatos irrelevantes
  de cada fonte ANTES do WRF para melhorar qualidade e performance.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/pre_wrf_filter_service.rb
    - Orquestra: EsScoreDropAnalyzer + PgvGapAnalyzer + WrfService
    - Log de quantos foram filtrados em cada etapa
  Testes:
    - RSpec: spec/services/search/pre_wrf_filter_service_spec.rb

DoD:
  - [ ] Pipeline implementado e testado
  - [ ] WRF recebe apenas candidatos pré-filtrados
  - [ ] Redução mensurável no volume do WRF
  - [ ] Métricas de filtragem por etapa

Criterios de Aceitacao:
  - [ ] ES filtra por taxa de queda
  - [ ] PGV filtra por gap semântico
  - [ ] WRF recebe união dos filtrados
  - [ ] Log com total por etapa

Dependencias: WDT-011, WDT-012
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-015

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: Elasticsearch + PG Vector

---

TAREFA: Orquestrar filtros estatísticos antes do WRF.

IMPLEMENTAÇÃO:

1. Service:
   app/services/search/pre_wrf_filter_service.rb

   class Search::PreWrfFilterService
     def initialize(es_results:, pgv_results:, qualification_level:)
       @es_results = es_results
       @pgv_results = pgv_results
       @level = qualification_level
     end

     def call
       filtered_es = Search::EsScoreDropAnalyzer.new(
         results: @es_results, qualification_level: @level
       ).analyze

       filtered_pgv = Search::PgvGapAnalyzer.new(
         results: @pgv_results, qualification_level: @level
       ).analyze

       log_filtering(filtered_es, filtered_pgv)

       Search::WrfService.new.merge(
         filtered_es, filtered_pgv,
         qualification_level: @level
       )
     end

     private

     def log_filtering(es, pgv)
       Rails.logger.info("[PreWRF] ES: #{@es_results.size}→#{es.size} | " \
         "PGV: #{@pgv_results.size}→#{pgv.size} | " \
         "WRF receives: #{es.size + pgv.size}")
     end
   end

NÃO FAZER:
- NÃO pular filtros se qualification_level não está definido (usar default :media)
- NÃO passar todos os candidatos ao WRF sem filtrar
```

---

# ÉPICO 17: BASE DE CRITÉRIOS DE AVALIAÇÃO (4 cards ativos + 3 cancelados, 26 SP)

> **Timing:** Pós-MVP, Sprints 6-10  
> **Impacto:** GAME CHANGER — Diferencial competitivo impossível de copiar  
> **Pré-requisito:** WDT-016 é independente (pode começar em paralelo)  
> **André classificou como:** "Coração do sistema"

> **⚠️ NOTA DE IMPLEMENTAÇÃO (08 Fev 2026):** A Fase 3 foi implementada no protótipo Replit com 4 cards core (WDT-016, WDT-018, WDT-021, WDT-022) e 34 testes unitários passando. 3 cards de interface admin (WDT-017, WDT-019, WDT-020) foram CANCELADOS conforme filosofia de design: o sistema é auto-evolutivo e auto-populado, sem necessidade de interfaces manuais ou workshops de RH.
>
> **Decisões de Design Fase 3:**
> - ✅ Auto-seed de critérios via TECH_SKILLS_CATALOG, BEHAVIORAL_COMPETENCIES_CATALOG, RESPONSIBILITIES_CATALOG (sem entrada manual)
> - ✅ Effectiveness score atualizado automaticamente via feedback (sem dashboard admin)
> - ✅ 8 mecanismos do André implementados: evidence classification, vague language detection, anomaly flags, essential exclusion, cap 99, floor rounding, confidence scoring, "do not infer" prompt
> - ❌ WDT-017 (Interface Admin) — cancelado: auto-população substitui gestão manual
> - ❌ WDT-019 (Dashboard Métricas) — cancelado: sistema se auto-ajusta sem supervisão manual
> - ❌ WDT-020 (Workshops RH) — cancelado: substituído por auto-seed de catálogos

---

### CARD WDT-016: Schema e Modelo da Base de Critérios

```yaml
Titulo: "[BE] Schema e modelo da base de critérios de avaliação"
Tipo: Story
Sprint: 6
Pontos: 8
Horas: 16
Prioridade: Crítica
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: criteria, game-changer, core

Descricao: |
  Criar schema do banco de dados para a base de critérios de avaliação.
  
  Contexto: André classificou como GAME CHANGER. Esta base será o coração 
  do sistema e diferencial competitivo impossível de copiar.
  
  Schema (ORIGINAL — ver Implementação Realizada abaixo):
  Table: evaluation_criteria
  - id (PK)
  - name (string) - ex: 'Senioridade em Tech'
  - category (string) - ex: 'Técnico', 'Comportamental', 'Liderança'
  - subcategory (string, nullable)
  - positive_evidences (jsonb) - array de evidências positivas
  - negative_evidences (jsonb) - array de evidências negativas
  - weight (integer, 1-10)
  - qualification_levels (array) - quais níveis se aplicam
  - effectiveness_score (float) - atualizado por aprendizado
  - status (enum) - rascunho/validado/arquivado
  - company_id (FK, nullable) - null = global, preenchido = company-specific

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit — Python/FastAPI):
  Modelo SQLAlchemy em lia-agent-system/app/models/evaluation_criteria.py
  Table: evaluation_criteria
  - id (UUID PK)
  - name (String 300, indexed)
  - category (String 50, indexed) — categories: technical_skill, behavioral_competency, experience, education, certification, language, responsibility
  - subcategory (String 100, nullable)
  - positive_evidences (JSONB) — array de evidências positivas
  - negative_evidences (JSONB) — array de evidências negativas
  - evaluation_guidelines (Text, nullable) — diretrizes de avaliação
  - effectiveness_score (Float, default 0.5) — atualizado automaticamente via feedback
  - usage_count (Integer, default 0)
  - feedback_count (Integer, default 0)
  - source (String 50, default "seed")
  - is_active (Boolean, default True) — substitui status enum (draft/validated/archived)
  - created_at, updated_at (DateTime)
  
  SEM: weight, qualification_levels, status enum, company_id
  Critérios são GLOBAIS, auto-populados dos catálogos existentes.
  
  Service em lia-agent-system/app/services/evaluation_criteria_service.py:
  - Auto-seed de TECH_SKILLS_CATALOG, BEHAVIORAL_COMPETENCIES_CATALOG, RESPONSIBILITIES_CATALOG
  - Evidence patterns por categoria (positive_templates, negative_templates, guideline_template)
  - Skill-specific evidence para Python, Java, React, AWS, SQL, Docker, Kubernetes, ML, Liderança, Comunicação
  - Fuzzy matching via SequenceMatcher para requirement→criteria lookup
  - Effectiveness auto-updated via feedback (update_effectiveness method)

Historia de Usuario: |
  Como plataforma, eu preciso de uma base estruturada de critérios 
  de avaliação para guiar a LLM na análise de candidatos com diretrizes
  claras e baseadas em expertise de RH sênior.

Requisitos Tecnicos:
  Backend (Rails):
    - Migration: db/migrate/xxx_create_evaluation_criteria.rb
    - Model: app/models/evaluation_criterion.rb
    - Controller: app/controllers/api/v1/evaluation_criteria_controller.rb
    - Serializer: app/serializers/evaluation_criterion_serializer.rb
    - Seeds: db/seeds/evaluation_criteria.rb (10 critérios exemplo)
    - Validações: name presence, weight 1-10, category inclusion

DoD:
  - [x] Migration executada (SQLAlchemy model no protótipo Replit)
  - [x] Modelo com validações (EvaluationCriteria SQLAlchemy)
  - [x] Auto-seed com catálogos existentes (TECH_SKILLS, BEHAVIORAL, RESPONSIBILITIES)
  - [x] Fuzzy matching para lookup de critérios
  - [x] Effectiveness auto-update via feedback
  - [ ] Modelo Rails com validações (produção — equipe externa)
  - [ ] CRUD API funcional (produção)
  - [ ] Testes de modelo e controller (produção)

Criterios de Aceitacao:
  - [x] Base de critérios auto-populada dos catálogos
  - [x] Evidence patterns por categoria
  - [x] Fuzzy matching funcional
  - [x] Effectiveness score atualizado via feedback
  - [ ] Scoping por company_id (produção — não necessário no protótipo)
  - [ ] Testes RSpec passando (produção)

Dependencias: Nenhuma
Bloqueia: WDT-018, WDT-021, WDT-022, WDT-027

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/models/evaluation_criteria.py
  - lia-agent-system/app/services/evaluation_criteria_service.py

Arquivos de Referencia (Prototipo Replit):
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - skills_catalog.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/skills_catalog.py
  - responsibilities_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/responsibilities_catalog_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-016

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL
- Testes: RSpec

---

TAREFA: Criar schema completo para base de critérios de avaliação.
ESTE É O GAME CHANGER — diferencial competitivo impossível de copiar.

IMPLEMENTAÇÃO:

1. Migration:
   create_table :evaluation_criteria do |t|
     t.string :name, null: false
     t.string :category, null: false  # Técnico, Comportamental, Liderança
     t.string :subcategory
     t.jsonb :positive_evidences, default: []  # ["5+ anos gerenciando equipes", ...]
     t.jsonb :negative_evidences, default: []  # ["Nunca liderou diretamente", ...]
     t.integer :weight, default: 5  # 1-10
     t.string :qualification_levels, array: true, default: []  # ["alta", "media"]
     t.float :effectiveness_score, default: 0.5  # 0-1, atualizado por aprendizado
     t.integer :status, default: 0  # enum: draft/validated/archived
     t.references :company, foreign_key: true, null: true  # null = global
     t.timestamps
   end
   add_index :evaluation_criteria, :category
   add_index :evaluation_criteria, :status
   add_index :evaluation_criteria, :company_id

2. Model:
   class EvaluationCriterion < ApplicationRecord
     enum status: { draft: 0, validated: 1, archived: 2 }
     validates :name, presence: true, uniqueness: { scope: :company_id }
     validates :weight, inclusion: { in: 1..10 }
     validates :category, inclusion: { in: %w[tecnico comportamental lideranca cultural] }
     scope :global, -> { where(company_id: nil) }
     scope :for_company, ->(id) { where(company_id: [nil, id]) }
     scope :for_level, ->(level) { where("? = ANY(qualification_levels)", level) }
     scope :active, -> { where(status: :validated) }
   end

3. Seeds com 10 critérios exemplo cobrindo:
   - Técnico: "Profundidade Técnica", "Arquitetura de Sistemas"
   - Comportamental: "Comunicação Executiva", "Adaptabilidade"
   - Liderança: "Gestão de Equipes", "Visão Estratégica"

NÃO FAZER:
- NÃO usar relação has_many para evidências (JSONB é mais flexível)
- NÃO esquecer company_id nullable (critérios globais vs company-specific)
```

---

### CARD WDT-017: Interface Admin para Gestão de Critérios — ❌ CANCELADO

> **❌ CANCELADO (08 Fev 2026):** Cancelado conforme filosofia de design: sistema auto-evolutivo sem interfaces de admin. Critérios são auto-populados dos catálogos existentes (TECH_SKILLS_CATALOG, BEHAVIORAL_COMPETENCIES_CATALOG, RESPONSIBILITIES_CATALOG) e auto-atualizados via feedback. Nenhuma entrada manual necessária.

```yaml
Titulo: "[FE] Interface admin para gestão de critérios"
Tipo: Story
Sprint: 7
Pontos: 8
Horas: 16
Prioridade: Alta
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ❌ Cancelado (não implementado)
Labels: criteria, admin, ux

Descricao: |
  Criar interface administrativa para RH sênior cadastrar e gerenciar 
  critérios de avaliação.
  
  Implementação:
  - Tela de listagem com filtros (categoria, peso, status)
  - Formulário de criação com campos dinâmicos para evidências
  - Adicionar/remover evidências positivas e negativas (array)
  - Seleção de peso e qualification_levels
  - Status: rascunho → validado
  - Busca e ordenação na listagem
  - Preview de como o critério será usado pelo LLM

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/EvaluationCriteria.vue
    - Componentes: CriterionForm.vue, CriterionCard.vue, EvidenceList.vue
    - Vuetify: v-data-table, v-dialog, v-chip-group, v-combobox

DoD:
  - [ ] CRUD completo funcional na UI
  - [ ] Campos dinâmicos para evidências
  - [ ] Filtros e busca na listagem
  - [ ] Workflow de validação
  - [ ] Responsivo

Criterios de Aceitacao:
  - [ ] Listar critérios com filtros funcionais
  - [ ] Criar critério com evidências dinâmicas
  - [ ] Editar e arquivar critérios
  - [ ] Mudar status draft → validated
  - [ ] Preview do prompt LLM

Dependencias: WDT-016
Bloqueia: WDT-020

Arquivos de Referencia (Prototipo Replit):
  - AdminTemplateHub.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/AdminTemplateHub.tsx
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - skills_catalog.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/skills_catalog.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-017

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest

---

TAREFA: Criar interface admin para gestão de critérios de avaliação.

IMPLEMENTAÇÃO:

1. Página principal: src/pages/admin/EvaluationCriteria.vue
   - v-data-table-server com colunas: Nome, Categoria, Peso, Status, Ações
   - Filtros: v-select categoria, v-slider peso, v-select status
   - v-text-field busca por nome
   - v-btn "Novo Critério" abre v-dialog com formulário

2. Formulário CriterionForm.vue:
   - v-text-field: nome
   - v-select: categoria (Técnico, Comportamental, Liderança, Cultural)
   - v-slider: peso (1-10)
   - v-chip-group: qualification_levels (Alta, Média, Baixa) - multi-select
   - EvidenceList (componente dinâmico):
     - Lista de v-text-field para cada evidência
     - v-btn "Adicionar evidência" (append)
     - v-btn icon "Remover" (splice)
     - Seção "Evidências Positivas" e "Evidências Negativas" separadas
   - Preview section: mostra como o critério será formatado no prompt LLM

3. EvidenceList.vue (componente reutilizável):
   - Props: modelValue (string[]), label, color
   - v-for com v-text-field para cada item
   - Botão adicionar/remover
   - Emit 'update:modelValue'

NÃO FAZER:
- NÃO usar textarea para evidências (uma por campo)
- NÃO permitir salvar sem pelo menos 1 evidência positiva
```

---

### CARD WDT-018: Integração de Critérios com Prompt da LLM

```yaml
Titulo: "[BE] Integração de critérios com prompt da LLM"
Tipo: Story
Sprint: 8
Pontos: 8
Horas: 14
Prioridade: Crítica
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: criteria, llm, core

Descricao: |
  Integrar a base de critérios com os prompts de avaliação da LLM (Gemini).
  
  Contexto: Injetar critérios relevantes no prompt para que a LLM tenha 
  diretrizes claras sobre o que constitui evidência forte, fraca ou negativa.
  
  Implementação (ORIGINAL):
  - Selecionar critérios relevantes baseado na vaga (categoria, qualification_level)
  - Formatar critérios como seção estruturada do prompt
  - Incluir evidências positivas e negativas como exemplos
  - Controlar tamanho do prompt (não injetar todos)
  - Ranking de critérios por relevância para a vaga
  - Benchmark de custo de tokens antes/depois

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit):
  Arquivo: lia-agent-system/app/services/rubric_evaluation_service.py
  - Método _format_criteria_examples() injeta critérios no RUBRIC_EVALUATION_PROMPT
  - Fuzzy matching via EvaluationCriteriaService.get_criteria_for_requirements()
  - Critérios formatados com evidências positivas E negativas como exemplos
  - Instrução "DO NOT INFER" explicitamente adicionada ao prompt
  - Classificação de tipo de evidência (explicit/implicit/inferred) requerida por requisito
  - Detecção de linguagem vaga dispara downgrade automático
  - Integração com metodologia de scoring do André

Requisitos Tecnicos:
  Backend (Python FastAPI):
    - Service: app/services/ai/criteria_prompt_builder.py
    - Selecionar top N critérios por relevância
    - Formatar como seção do prompt
    - Controlar max_tokens dedicados a critérios (< 20% do prompt total)
  Testes:
    - pytest: tests/test_criteria_prompt_builder.py

DoD:
  - [ ] Critérios injetados no prompt dinamicamente
  - [ ] Seleção inteligente por relevância
  - [ ] Custo de tokens controlado (< 20% aumento)
  - [ ] Melhoria mensurável na qualidade das avaliações
  - [ ] Testes A/B com/sem critérios

Criterios de Aceitacao:
  - [ ] Prompt inclui critérios relevantes para a vaga
  - [ ] Max 10 critérios por prompt (controle de tokens)
  - [ ] Evidências positivas e negativas incluídas
  - [ ] Custo de tokens < 20% aumento vs. sem critérios

Dependencias: WDT-016
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - nodes.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/agents/nodes.py
  - job_wizard_tools.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/tools/job_wizard_tools.py

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/services/rubric_evaluation_service.py (linhas ~524-556 para _format_criteria_examples, linhas ~327-520 para RUBRIC_EVALUATION_PROMPT)
```

#### Prompt para IA (Cursor/VSCode) — WDT-018

```
CONTEXTO DO PROJETO WEDO TALENT:
- IA: Python 3.11 + FastAPI + LangChain + Gemini 2.5 Flash
- Banco: PostgreSQL (acessado via Rails API)

---

TAREFA: Integrar base de critérios com prompts de avaliação da LLM.

IMPLEMENTAÇÃO:

1. Service Python:
   app/services/ai/criteria_prompt_builder.py

   class CriteriaPromptBuilder:
     MAX_CRITERIA = 10
     
     def build(self, job_data: dict, criteria: list[dict]) -> str:
       relevant = self._select_relevant(job_data, criteria)
       return self._format_prompt_section(relevant[:self.MAX_CRITERIA])
     
     def _select_relevant(self, job_data, criteria):
       level = job_data.get('qualification_level', 'media')
       category_match = [c for c in criteria 
                         if level in c['qualification_levels']]
       return sorted(category_match, key=lambda c: -c['weight'])
     
     def _format_prompt_section(self, criteria):
       sections = []
       for c in criteria:
         sections.append(f"""
         CRITÉRIO: {c['name']} (Peso: {c['weight']}/10)
         Categoria: {c['category']}
         Evidências FORTES (o que procurar): {', '.join(c['positive_evidences'])}
         Evidências FRACAS (sinais negativos): {', '.join(c['negative_evidences'])}
         """)
       return "\\n".join(sections)

2. Injeção no prompt principal de avaliação:
   - Adicionar seção "CRITÉRIOS DE AVALIAÇÃO" antes das instruções de análise
   - LLM deve referenciar critérios na justificativa

NÃO FAZER:
- NÃO injetar todos os critérios (controlar tokens)
- NÃO chamar Rails DB diretamente do Python (usar API)
```

---

### CARD WDT-019: Dashboard de Gestão e Métricas de Critérios — ❌ CANCELADO

> **❌ CANCELADO (08 Fev 2026):** Cancelado conforme filosofia de design: inteligência auto-evolutiva sem dashboards de admin. Effectiveness score é atualizado automaticamente via feedback. Métricas são coletadas de forma transparente pelo sistema.

```yaml
Titulo: "[BE/FE] Dashboard de gestão e métricas de critérios"
Tipo: Story
Sprint: 9
Pontos: 5
Horas: 10
Prioridade: Média
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ❌ Cancelado (não implementado)
Labels: criteria, analytics

Descricao: |
  Dashboard para acompanhar uso e efetividade dos critérios.
  
  Métricas:
  - Critérios mais utilizados
  - Critérios com melhor taxa de like/dislike
  - Cobertura de critérios por categoria de vaga
  - Critérios sem uso (candidatos a remoção)
  - Evolução ao longo do tempo

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/analytics/criteria_analytics_service.rb
    - Queries agregadas cruzando critérios com feedbacks
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/CriteriaDashboard.vue
    - Gráficos com ApexCharts

DoD:
  - [ ] Dashboard funcional e responsivo
  - [ ] Métricas atualizadas em real-time
  - [ ] Filtros por período e categoria

Criterios de Aceitacao:
  - [ ] Top 10 critérios mais usados exibidos
  - [ ] Taxa de efetividade por critério
  - [ ] Critérios sem uso destacados
  - [ ] Filtros funcionais

Dependencias: WDT-016, WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - AdminTemplateHub.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/AdminTemplateHub.tsx
  - strategic-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/strategic-dashboard.tsx
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-019

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3
- Cache: Redis

---

TAREFA: Criar dashboard de métricas de critérios de avaliação.

IMPLEMENTAÇÃO:

Backend:
- Service cruzando evaluation_criteria com candidate_feedbacks
- Métricas: uso por critério, efetividade (like rate quando critério usado),
  cobertura por categoria, critérios sem uso

Frontend:
- ApexCharts para gráficos de barras e donut
- v-data-table para listagem detalhada
- Filtros por período e categoria
```

---

### CARD WDT-020: Alimentação Inicial com RH Sênior — ❌ CANCELADO / SUBSTITUÍDO

> **❌ CANCELADO / SUBSTITUÍDO (08 Fev 2026):** Substituído por auto-seed automático dos catálogos existentes. O sistema se auto-popula com critérios gerados a partir de TECH_SKILLS_CATALOG (~hundreds de skills), BEHAVIORAL_COMPETENCIES_CATALOG (~dozens de competências com subcategories), e RESPONSIBILITIES_CATALOG. Nenhum workshop manual ou importação CSV necessária. Evidence patterns são gerados automaticamente com templates por categoria.

```yaml
Titulo: "[DATA] Alimentação inicial: 50-100 critérios com RH sênior"
Tipo: Task
Sprint: 9-10
Pontos: 13
Horas: 40
Prioridade: Alta
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ❌ Cancelado / Substituído
Labels: criteria, data, onboarding

Descricao: |
  Workshop com equipe de RH sênior da Talenses para alimentar a base 
  inicial de critérios.
  
  Atividades:
  - 3-4 sessões de 2h com RH sênior
  - Mapear critérios para vagas de alta, média e baixa qualificação
  - Definir evidências positivas e negativas para cada critério
  - Validar pesos e categorias
  - Documentar processo para futuras alimentações
  
  Meta: 50-100 critérios validados cobrindo as principais categorias.

Requisitos Tecnicos:
  Processo:
    - Template de captura: planilha/formulário padronizado
    - Script de importação: lib/tasks/import_criteria.rake
    - Validação automática de formato e completude
  Dados:
    - Critérios cobrindo todas as categorias: Técnico, Comportamental, Liderança, Cultural
    - Critérios para os 3 níveis de qualificação
    - Mínimo 3 evidências positivas e 2 negativas por critério

DoD:
  - [ ] Mínimo 50 critérios cadastrados e validados
  - [ ] Cobertura de todas as categorias principais
  - [ ] Critérios para os 3 níveis de qualificação
  - [ ] Documentação do processo

Criterios de Aceitacao:
  - [ ] 50+ critérios com status "validated"
  - [ ] Cada critério com 3+ evidências positivas
  - [ ] Cada critério com 2+ evidências negativas
  - [ ] Cobertura dos 3 níveis (alta, média, baixa)
  - [ ] Processo documentado para futuras sessões

Dependencias: WDT-017
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - template_importer_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/template_importer_service.py
  - learning_loop_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/learning_loop_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-020

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x

---

TAREFA: Criar script de importação massiva de critérios de avaliação.

IMPLEMENTAÇÃO:

1. Rake task: lib/tasks/import_criteria.rake
   - Ler CSV/XLSX com colunas: nome, categoria, subcategoria, evidencias_positivas,
     evidencias_negativas, peso, niveis_qualificacao
   - Validar formato e completude
   - Criar registros via EvaluationCriterion
   - Log de importação com sucesso/erros

2. Template CSV para workshops:
   name,category,subcategory,positive_evidences,negative_evidences,weight,levels
   "Senioridade Tech","tecnico","","5+ anos|Liderou projetos","Sem experiência",8,"alta,media"

3. Validações na importação:
   - Nome obrigatório e único
   - Mínimo 3 evidências positivas
   - Mínimo 2 evidências negativas
   - Peso 1-10
   - Categoria válida

NÃO FAZER:
- NÃO importar sem validação
- NÃO sobrescrever critérios existentes sem flag --force
```

---

### CARD WDT-021: Sistema de Classificação Explicit/Implicit/Inferred

```yaml
Titulo: "[BE] Sistema de classificação Explicit/Implicit/Inferred"
Tipo: Story
Sprint: 10
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: evidence, llm, quality

Descricao: |
  Implementar sistema de tipos de evidência na avaliação LLM.
  
  Contexto: André propôs 3 níveis:
  - Explicit: candidato atende critério conforme diretriz (mais confiável)
  - Implicit: parece atender mas sem confirmação direta
  - Inferred: LLM inferiu baseado em interpretação (perigoso)
  
  Implementação (ORIGINAL):
  - Atualizar prompt para LLM retornar match_level por requisito
  - Schema: {requirement, match_level, evidence_text, confidence}
  - Requisitos essenciais: apenas 'explicit' aceito
  - Diferenciais: 'implicit' e 'inferred' aceitos com peso reduzido
  - Filtrar/penalizar 'inferred' automaticamente no score

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit — todos os 8 mecanismos do André):
  1. EvidenceType enum (explicit, implicit, inferred) em app/schemas/rubric.py
  2. Evidence weights: explicit=1.0, implicit=0.7, inferred=0.3
  3. Detecção de linguagem vaga: 18 indicadores bilíngues
     PT: "pode ter", "indica que", "sugere", "provavelmente", "talvez", "aparentemente", "possivelmente", "parece que", "supostamente"
     EN: "probably", "suggests", "may have", "might", "possibly", "appears to", "seems", "likely", "could have"
  4. Auto-downgrade: linguagem vaga → evidence_type vira "inferred" com confidence máx 0.3
  5. Anomaly flags: exceeds_ratio (>80% exceeds), skills_ratio (competencies_count < skills_matched), inferred_meets_exceeds (inferred mas meets/exceeds), low_experience_high_score
  6. Regra de exclusão essential: se QUALQUER requisito essential tem level="missing" OU (level="partial/meets/exceeds" E evidence_type!="explicit") → auto_excluded=True, score=0 antes do WRF
  7. Confidence scoring: 0.0-1.0 por requisito

Requisitos Tecnicos:
  Backend (Python FastAPI):
    - Atualizar prompt de avaliação
    - Pydantic model para resposta estruturada
    - Penalização: explicit=1.0, implicit=0.7, inferred=0.3
  Testes:
    - pytest com diferentes tipos de currículos

DoD:
  - [x] LLM retorna match_level para cada requisito (EvidenceType enum)
  - [x] Filtro de essenciais apenas com explicit (regra de exclusão automática)
  - [x] Penalização de inferred implementada (EVIDENCE_WEIGHTS)
  - [x] Detecção de linguagem vaga (18 indicadores bilíngues)
  - [x] Anomaly flags implementados
  - [x] Testes passando (34 testes, 13 classes)

Criterios de Aceitacao:
  - [x] Resposta inclui evidence_type para cada requisito
  - [x] Requisitos essenciais rejeitam implicit/inferred (auto-exclusão)
  - [x] Score penalizado para inferred (weight 0.3)
  - [x] Linguagem vaga detectada e downgradada automaticamente
  - [x] Anomaly flags gerados para padrões suspeitos
  - [x] Testes passando

Dependencias: WDT-016
Bloqueia: WDT-022, WDT-023

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
  - confidence_policy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/confidence_policy_service.py

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/schemas/rubric.py (EvidenceType enum, RequirementEvaluation com evidence_type/confidence/vague_language_detected/anomaly_flags)
  - lia-agent-system/app/services/rubric_evaluation_service.py (_detect_vague_language, _detect_anomalies, evidence weight application)
```

#### Prompt para IA (Cursor/VSCode) — WDT-021

```
CONTEXTO DO PROJETO WEDO TALENT:
- IA: Python 3.11 + FastAPI + LangChain + Gemini 2.5 Flash

---

TAREFA: Implementar classificação de tipo de evidência (Explicit/Implicit/Inferred).

IMPLEMENTAÇÃO:

1. Pydantic model:
   class RequirementMatch(BaseModel):
     requirement: str
     match_level: Literal["explicit", "implicit", "inferred"]
     evidence_text: str
     confidence: float  # 0-1

2. Prompt atualizado:
   "Para cada requisito, classifique o nível de evidência:
   - EXPLICIT: O currículo CONFIRMA diretamente este requisito com dados concretos
   - IMPLICIT: O currículo SUGERE este requisito mas sem confirmação direta
   - INFERRED: Você está INFERINDO com base em interpretação (MARQUE COMO TAL)
   
   REGRA: Para requisitos ESSENCIAIS, apenas EXPLICIT é aceito."

3. Penalização no score:
   WEIGHTS = {"explicit": 1.0, "implicit": 0.7, "inferred": 0.3}
   adjusted_score = raw_score * WEIGHTS[match_level]

NÃO FAZER:
- NÃO aceitar inferred para requisitos essenciais
- NÃO tratar implicit e explicit como iguais
```

---

### CARD WDT-022: Score de Confiança Individual por Requisito

```yaml
Titulo: "[BE/FE] Score de confiança individual por requisito"
Tipo: Story
Sprint: 11
Pontos: 5
Horas: 10
Prioridade: Média
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: evidence, transparency

Descricao: |
  Implementar score individual por requisito ao invés de score único.
  
  Implementação (ORIGINAL):
  - LLM retorna score 0-100 por requisito obrigatório
  - Armazenar breakdown: {requirement: score, match_level, evidence}
  - UI: expandir card do candidato para ver breakdown
  - Score total = média ponderada dos individuais

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit — fórmulas do André):
  - adjusted_score = points × EVIDENCE_WEIGHTS[evidence_type]
  - final_score = min(99.0, floor(Σ(score_i × weight_i × evidence_weight_i) / Σ(100 × weight_i)))
  - Cap 99: score máximo nunca é 100 (garante margem para revisão humana)
  - Floor rounding: scores arredondados para inteiros (elimina ruído decimal, ex: 84.98 → 84)
  - raw_score: preservado para transparência antes de cap/floor
  - Auto-exclusão: requisito essential com missing ou evidence não-explicit → score=0, auto_excluded=True
  - Scoring methodology tagged como "andre_v1"
  - RubricEvaluationResult schema inclui: score, raw_score, auto_excluded, exclusion_reasons, anomaly_flags, scoring_methodology
  - 34 testes unitários passando cobrindo todos os 8 mecanismos do André

Requisitos Tecnicos:
  Backend:
    - Atualizar response schema do avaliador LLM
    - Salvar breakdown no JSONB do candidate_evaluation
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/candidates/ScoreBreakdown.vue
    - v-expansion-panel para expandir detalhes
    - v-progress-linear por requisito com cor por match_level

DoD:
  - [x] Score por requisito retornado (RequirementEvaluation schema)
  - [x] Fórmula de scoring com evidence weights implementada
  - [x] Cap 99 com floor rounding
  - [x] Auto-exclusão para essential com missing/non-explicit evidence
  - [x] raw_score preservado para transparência
  - [x] 34 testes passando (13 classes de teste)
  - [ ] UI com breakdown expansível (produção — equipe externa)

Criterios de Aceitacao:
  - [x] Cada requisito com score individual e evidence_type
  - [x] Score ajustado por evidence weights (1.0/0.7/0.3)
  - [x] Cap 99 e floor rounding funcionando
  - [x] Auto-exclusão por requisitos essential
  - [x] Methodology tagged como "andre_v1"
  - [ ] Card expandível mostrando detalhes (produção)

Dependencias: WDT-021
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
  - confidence_policy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/confidence_policy_service.py
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/services/rubric_evaluation_service.py (scoring logic, _calculate_score method)
  - lia-agent-system/app/schemas/rubric.py (RubricEvaluationResult schema com score, raw_score, auto_excluded, exclusion_reasons, anomaly_flags, scoring_methodology)
  - lia-agent-system/tests/test_phase3_andre_methodology.py (34 testes, 13 classes de teste)
```

#### Prompt para IA (Cursor/VSCode) — WDT-022

```
CONTEXTO DO PROJETO WEDO TALENT:
- Backend: Python FastAPI + Rails
- Frontend: Vue.js 3 + Vuetify 3

---

TAREFA: Implementar score individual por requisito com breakdown visual.

IMPLEMENTAÇÃO:

Backend (Python):
- LLM retorna: [{ requirement, score: 0-100, match_level, evidence_text }]
- Score total: soma ponderada (peso do requisito * score * weight_match_level) / soma pesos

Frontend (Vue):
- ScoreBreakdown.vue:
  - v-expansion-panels para expandir card do candidato
  - Para cada requisito: v-progress-linear com cor:
    - explicit: color="success"
    - implicit: color="warning"
    - inferred: color="error"
  - Label: "{requisito}: {score}% ({match_level})"
  - evidence_text em v-card-text

NÃO FAZER:
- NÃO mostrar apenas score total sem breakdown
```

---

### FASE 3 — ARQUIVOS IMPLEMENTADOS NO PROTÓTIPO REPLIT

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/models/evaluation_criteria.py` | Modelo SQLAlchemy: EvaluationCriteria com JSONB positive/negative evidences |
| `lia-agent-system/app/services/evaluation_criteria_service.py` | Service: auto-seed, fuzzy matching, effectiveness update |
| `lia-agent-system/app/services/rubric_evaluation_service.py` | Integração com prompt LLM, scoring André, vague language, anomalies |
| `lia-agent-system/app/schemas/rubric.py` | Schemas Pydantic: EvidenceType, RequirementEvaluation, RubricEvaluationResult |
| `lia-agent-system/tests/test_phase3_andre_methodology.py` | 34 testes unitários, 13 classes de teste |

**Mecanismos do André Implementados:**
1. ✅ Base de evidências positivas/negativas para prompts (WDT-016)
2. ✅ Classificação explicit/implicit/inferred com pesos 1.0/0.7/0.3 (WDT-021)
3. ✅ Detecção de linguagem vaga — 18 indicadores bilíngues PT/EN (WDT-021)
4. ✅ Flags de anomalia — exceeds_ratio, skills_ratio, inferred meets/exceeds, low experience (WDT-021)
5. ✅ Exclusão automática — essential missing OR essential com evidence!=explicit → score=0 (WDT-022)
6. ✅ Cap 99 com floor rounding (WDT-022)
7. ✅ Confidence score por requisito 0.0-1.0 (WDT-021)
8. ✅ Instrução explícita "DO NOT INFER" no prompt (WDT-018)

---

# ÉPICO 18: APRENDIZADO E FEATURES AVANÇADAS (6 cards, 42 SP)

> **Timing:** Pós-MVP, Sprints 12-17  
> **Impacto:** Sistema auto-evolutivo + features de alto valor para executive search  
> **Pré-requisito:** Épico 17 (Base de Critérios) e Like/Dislike (WDT-006)

---

### CARD WDT-023: Toggle de Requisito Essencial Excludente

```yaml
Titulo: "[BE/FE] Toggle de requisito essencial excludente"
Tipo: Story
Sprint: 12
Pontos: 5
Horas: 8
Prioridade: Alta
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: requirements, filter, quality

Descricao: |
  Permitir que recrutador marque requisitos como excludentes (no-go).
  
  Contexto: André questionou se 'essencial' é excludente ou apenas valorizado.
  
  Implementação:
  - Toggle na UI de criação de vaga: 'Este requisito é excludente'
  - Backend: se requisitos_essenciais_atendidos < threshold, excluir candidato
  - Excluir ANTES do WRF (economia de processamento)
  - Log de candidatos excluídos por requisitos não atendidos

Requisitos Tecnicos:
  Backend (Rails):
    - Adicionar campo is_excludent (boolean) no modelo JobRequirement
    - Filtro pré-WRF: verificar requisitos excludentes com match_level=explicit
  Frontend (Vue.js 3 + Vuetify 3):
    - v-switch no formulário de requisitos da vaga
    - Label: "Excludente (candidato sem este requisito será eliminado)"

DoD:
  - [ ] Toggle funcional na criação de vaga
  - [ ] Candidatos excluídos antes do WRF
  - [ ] Log de exclusões acessível
  - [ ] Threshold configurável

Criterios de Aceitacao:
  - [ ] Toggle visível e funcional
  - [ ] Candidatos sem requisito excludente não aparecem
  - [ ] Exclusão antes do WRF (economia)
  - [ ] Log com candidatos excluídos

Dependencias: WDT-021
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - advanced-search.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/advanced-search.tsx
  - SkillsFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/SkillsFilterInput.tsx
```

#### Prompt para IA (Cursor/VSCode) — WDT-023

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3

---

TAREFA: Implementar toggle de requisito excludente na criação de vaga.

IMPLEMENTAÇÃO:

Backend (Rails):
1. Migration: add_column :job_requirements, :is_excludent, :boolean, default: false
2. No pipeline de busca, antes do WRF:
   - Verificar se candidato atende TODOS requisitos excludentes com match_level=explicit
   - Se não atende, excluir do pipeline
   - Log: "[Excludent] Candidate #{id} excluded: missing #{requirement}"

Frontend (Vue):
1. No formulário de requisitos da vaga:
   v-switch v-model="requirement.is_excludent"
   label="Excludente" hint="Candidato será eliminado sem este requisito"
   color="error"
```

---

### CARD WDT-024: Enriquecimento de Perfil Sob Demanda via Web

```yaml
Titulo: "[BE] Enriquecimento de perfil sob demanda via web"
Tipo: Story
Sprint: 13
Pontos: 8
Horas: 16
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: enrichment, executive-search

Descricao: |
  Permitir enriquecer perfil de candidato com informações da web.
  
  Fontes:
  - Google Scholar (publicações acadêmicas)
  - Escavador (referências jurídicas/acadêmicas)
  - Busca web geral (entrevistas, palestras, artigos)
  
  Implementação:
  - Botão 'Enriquecer perfil' no card do candidato
  - Background job (Sidekiq) para scraping
  - LLM analisa e estrutura informações encontradas
  - Salvar enriquecimento vinculado ao perfil
  - Rate limiting e controle de custos

Requisitos Tecnicos:
  Backend (Rails):
    - Job: app/jobs/profile_enrichment_job.rb (Sidekiq)
    - Service: app/services/candidates/profile_enrichment_service.rb
    - Model: app/models/candidate_enrichment.rb
    - Fontes: Google Scholar API, Escavador, SerpAPI
  Python (FastAPI):
    - Endpoint para análise LLM do conteúdo coletado
  Frontend (Vue.js 3 + Vuetify 3):
    - Botão "Enriquecer perfil" no card do candidato
    - Status: pendente → processando → concluído
    - Expandir card para ver dados enriquecidos

DoD:
  - [ ] Botão funcional na UI
  - [ ] Enriquecimento async via job Sidekiq
  - [ ] Informações estruturadas e salvas
  - [ ] Controle de custos implementado

Criterios de Aceitacao:
  - [ ] Botão dispara job em background
  - [ ] Status atualizado em real-time (ActionCable/polling)
  - [ ] Dados enriquecidos visíveis no perfil
  - [ ] Rate limit: max 10 enriquecimentos/hora por company

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - candidate_enrichment_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_enrichment_service.py
  - pearch_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pearch_service.py
  - apify_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/apify_service.py
  - sourcing.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/sourcing.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-024

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Python FastAPI
- Background Jobs: Sidekiq + Redis
- IA: Gemini 2.5 Flash

---

TAREFA: Criar sistema de enriquecimento de perfil de candidato via web.

IMPLEMENTAÇÃO:

1. Job Sidekiq: app/jobs/profile_enrichment_job.rb
   - Recebe: candidate_id, company_id
   - Executa: busca em fontes web → LLM estrutura → salva
   - Rate limit: max 10/hora por company (Redis counter)

2. Service: app/services/candidates/profile_enrichment_service.rb
   - Busca Google Scholar via SerpAPI
   - Busca geral via SerpAPI
   - Envia conteúdo para FastAPI: POST /api/v1/ai/enrich-profile
   - LLM estrutura: publicações, palestras, menções, artigos

3. Model: CandidateEnrichment
   - candidate_id, source, raw_data (jsonb), structured_data (jsonb),
     status (pending/processing/completed/failed), created_at

ATENÇÃO LEGAL:
- Não fazer scraping de LinkedIn (violação ToS)
- Usar apenas fontes públicas
- Respeitar robots.txt
```

---

### CARD WDT-025: Análise Pós-Busca com Feedback de Qualidade

```yaml
Titulo: "[BE/FE] Análise pós-busca com feedback de qualidade"
Tipo: Story
Sprint: 13
Pontos: 5
Horas: 10
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: feedback, ux, quality

Descricao: |
  Após retornar 10 candidatos, LLM analisa qualidade geral e dá feedback.
  
  Implementação:
  - LLM avalia os 10 resultados como conjunto
  - Retorna: 'Resultados OK' ou 'Sugestão: refine sua busca'
  - Sugestões concretas de refinamento
  - Modal com feedback e sugestões
  - Botão 'Aplicar sugestão' para refinar automaticamente

Requisitos Tecnicos:
  Backend (Python FastAPI):
    - Endpoint: POST /api/v1/ai/analyze-search-quality
    - Recebe: candidatos retornados, query original, vaga
    - Retorna: quality_score, suggestions[], is_satisfactory
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: SearchQualityFeedback.vue
    - v-dialog com sugestões
    - v-btn "Aplicar sugestão" para cada sugestão

DoD:
  - [ ] Análise automática após busca
  - [ ] Feedback claro ao usuário
  - [ ] Sugestões de refinamento concretas
  - [ ] Modal funcional

Criterios de Aceitacao:
  - [ ] Análise executa após cada busca
  - [ ] Sugestões específicas (não genéricas)
  - [ ] Botão "Aplicar" funcional
  - [ ] Não bloqueia fluxo (assíncrono)

Dependencias: WDT-016
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - feedback_learning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feedback_learning_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-025

```
CONTEXTO DO PROJETO WEDO TALENT:
- IA: Python FastAPI + Gemini 2.5 Flash
- Frontend: Vue.js 3 + Vuetify 3

---

TAREFA: Criar análise pós-busca com feedback de qualidade.

IMPLEMENTAÇÃO:

Backend (Python):
- Endpoint: POST /api/v1/ai/analyze-search-quality
- Prompt: "Analise estes 10 candidatos retornados para a vaga '{title}'.
  Avalie: diversidade de perfis, cobertura de requisitos, gaps evidentes.
  Retorne: { quality_score: 0-100, is_satisfactory: bool,
  suggestions: [{ text: 'Considere ampliar...', action: 'add_keyword:python' }] }"

Frontend (Vue):
- Componente que aparece após resultados carregarem
- v-alert type="info" se satisfatório
- v-dialog com lista de sugestões se não satisfatório
- v-btn para cada sugestão que modifica a query automaticamente
```

---

### CARD WDT-026: Flags Automáticas de Inconsistência

```yaml
Titulo: "[BE] Flags automáticas de inconsistência"
Tipo: Story
Sprint: 14
Pontos: 3
Horas: 6
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: quality, flags, heuristics

Descricao: |
  Implementar flags automáticas para detectar inconsistências na avaliação.
  
  Regras heurísticas:
  - Currículo com < 3 competências marcado como 'exceeded' em 5+ requisitos
  - Currículo com < 50 palavras atendendo requisitos complexos
  - Score > 95% em vaga altamente qualificada com perfil incompleto
  - Discrepância > 40% entre score ES e score PGV para mesmo candidato

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/inconsistency_detector.rb
    - Flag model ou campo JSONB no candidate_evaluation
    - Regras configuráveis (não hardcoded)
  Frontend:
    - v-chip color="warning" icon="mdi-alert" no card do candidato flagado

DoD:
  - [ ] Regras heurísticas implementadas
  - [ ] Flag visível no card do candidato
  - [ ] Candidatos flagados separados/destacados
  - [ ] Dashboard de anomalias

Criterios de Aceitacao:
  - [ ] 4 regras heurísticas implementadas
  - [ ] Flags visíveis no card
  - [ ] Admin pode ver todos os flagados
  - [ ] Regras configuráveis

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - proactive_alert_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/proactive_alert_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-026

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL

---

TAREFA: Implementar detecção automática de inconsistências em avaliações.

IMPLEMENTAÇÃO:

1. Service: app/services/search/inconsistency_detector.rb

   RULES = [
     { name: "low_competencies_high_score",
       condition: ->(eval) { eval.competencies_count < 3 && eval.exceeded_count >= 5 },
       message: "Poucas competências mas muitos requisitos excedidos" },
     { name: "short_cv_complex_match",
       condition: ->(eval) { eval.cv_word_count < 50 && eval.complex_requirements_met > 3 },
       message: "CV muito curto atendendo requisitos complexos" },
     { name: "suspiciously_high_score",
       condition: ->(eval) { eval.score > 95 && eval.qualification_level == 'alta' && eval.profile_incomplete? },
       message: "Score muito alto para perfil incompleto em vaga executive" },
     { name: "source_score_discrepancy",
       condition: ->(eval) { (eval.es_score - eval.pgv_score).abs > 40 },
       message: "Discrepância significativa entre ES e PGV" }
   ]

2. Executar após cada avaliação, salvar flags em JSONB
3. Frontend: v-chip color="warning" no card com tooltip da mensagem
```

---

### CARD WDT-027: Motor de Aprendizado via Feedback

```yaml
Titulo: "[BE] Motor de aprendizado via feedback (Like/Dislike)"
Tipo: Story
Sprint: 15-16
Pontos: 13
Horas: 24
Prioridade: Alta
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 5 - Aprendizado
Status: 📋 Pendente Jira
Labels: learning, evolution, core

Descricao: |
  Construir motor de análise de padrões nos feedbacks para evolução automática.
  
  Implementação:
  - Análise de correlação: quais critérios geram mais likes?
  - Identificar padrões de dislike por tipo de vaga
  - Sugestão de ajuste de thresholds baseada em dados
  - Atualização do effectiveness_score dos critérios
  - Pipeline: feedback → análise → sugestão → aprovação humana → aplicação

Requisitos Tecnicos:
  Backend (Rails + Python):
    - Rails Job: app/jobs/learning_analysis_job.rb (semanal)
    - Python Service: app/services/ai/learning_engine.py
    - Correlação: critérios × feedback × tipo vaga × qualification_level
    - Output: sugestões de ajuste com confiança
    - Aprovação humana obrigatória antes de aplicar
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/LearningInsights.vue
    - Lista de sugestões pendentes com botão aprovar/rejeitar

DoD:
  - [ ] Pipeline funcional end-to-end
  - [ ] Sugestões de ajuste geradas automaticamente
  - [ ] Aprovação humana antes de aplicar
  - [ ] Métricas de evolução do sistema

Criterios de Aceitacao:
  - [ ] Job semanal executa e gera insights
  - [ ] Sugestões com confiança e justificativa
  - [ ] Admin aprova/rejeita sugestões
  - [ ] effectiveness_score atualizado após aprovação

Dependencias: WDT-006, WDT-016
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - feedback_learning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feedback_learning_service.py
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - learning_loop_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/learning_loop_service.py
  - pattern_detector_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pattern_detector_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-027

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Python 3.11 + FastAPI
- Background Jobs: Sidekiq
- IA: Gemini 2.5 Flash

---

TAREFA: Criar motor de aprendizado baseado em feedbacks like/dislike.

IMPLEMENTAÇÃO:

1. Job semanal (Sidekiq):
   app/jobs/learning_analysis_job.rb
   - Coleta feedbacks da última semana
   - Envia para Python: POST /api/v1/ai/analyze-feedback-patterns
   - Salva sugestões como LearningInsight records

2. Python Service:
   app/services/ai/learning_engine.py
   - Correlaciona: critérios usados × feedback recebido
   - Identifica: "critério X tem 80% dislike em vagas operacionais"
   - Gera: sugestão de ajuste com confiança e justificativa
   - Pipeline: human-in-the-loop (NUNCA aplicar automaticamente)

3. Model: LearningInsight
   - suggestion_type (threshold_adjust/weight_change/criteria_retire)
   - target (evaluation_criterion_id ou parameter name)
   - current_value, suggested_value, confidence, reasoning
   - status (pending/approved/rejected)
   - approved_by (user_id)

4. Frontend: lista de sugestões com approve/reject

NÃO FAZER:
- NUNCA aplicar ajustes automaticamente — sempre aprovação humana
- NÃO gerar sugestões com < 50 feedbacks de base
```

---

### CARD WDT-028: Framework de A/B Testing de Parâmetros

```yaml
Titulo: "[BE] Framework de A/B testing de parâmetros"
Tipo: Story
Sprint: 17
Pontos: 8
Horas: 14
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 5 - Aprendizado
Status: 📋 Pendente Jira
Labels: ab-testing, optimization

Descricao: |
  Criar framework para testar diferentes configurações de parâmetros.
  
  Parâmetros testáveis: K (WRF), thresholds, pesos de critérios, prompts.
  
  Implementação:
  - Config de experimentos (% tráfego, variantes)
  - Tracking de qual variante foi usada em cada busca
  - Análise estatística de resultados (p-value, confiança)
  - Dashboard de experimentos

Requisitos Tecnicos:
  Backend (Rails):
    - Model: app/models/experiment.rb
    - Service: app/services/experiments/ab_test_service.rb
    - Tracking: salvar experiment_variant_id em cada busca
    - Análise: estatística básica (média, desvio, p-value)
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/Experiments.vue
    - Criar/gerenciar experimentos
    - Dashboard de resultados

DoD:
  - [ ] Framework funcional
  - [ ] Pelo menos 1 experimento executado
  - [ ] Análise estatística automatizada
  - [ ] Dashboard de resultados

Criterios de Aceitacao:
  - [ ] Criar experimento com variantes
  - [ ] Tráfego distribuído conforme config
  - [ ] Tracking de variante por busca
  - [ ] Relatório com p-value

Dependencias: WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - feature_flag_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feature_flag_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-028

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3
- Cache: Redis

---

TAREFA: Criar framework de A/B testing para parâmetros de busca.

IMPLEMENTAÇÃO:

1. Model Experiment:
   - name, description, status (draft/running/completed)
   - parameter_name (ex: "wrf_k", "es_threshold")
   - variants (jsonb): [{ name: "control", value: 60, traffic: 50 }, 
                         { name: "variant_a", value: 30, traffic: 50 }]
   - start_date, end_date, min_sample_size

2. Service: app/services/experiments/ab_test_service.rb
   - assign_variant(experiment_id, user_id): usa hash para distribuição estável
   - get_parameter(parameter_name, user_id): retorna valor da variante
   - Salvar variant_id em cada search record

3. Dashboard:
   - Listar experimentos com status
   - Para cada: métricas (like_rate, score_mean) por variante
   - Análise estatística básica

NÃO FAZER:
- NÃO mudar variante de um usuário no meio do experimento
- NÃO rodar A/B sem sample size mínimo
```

---

# ÉPICO 19: OBSERVABILIDADE E DOCUMENTAÇÃO DE BUSCA (2 cards, 16 SP)

> **Timing:** Transversal, Sprint 2+ e Sprint 18  
> **Impacto:** Manutenibilidade, troubleshooting, onboarding de novos devs  
> **Pré-requisito:** Nenhum (documentação) / WDT-011/012/013 (dashboard)

---

### CARD WDT-029: Documentação Técnica Completa do Sistema de Busca

```yaml
Titulo: "[DOC] Documentação técnica completa do sistema de busca"
Tipo: Task
Sprint: 2+
Pontos: 8
Horas: 16
Prioridade: Média
Epic: EPIC-19 (Observabilidade e Documentação de Busca)
Fase: Fase 6 - Docs & Infra
Status: 📋 Pendente Jira
Labels: docs, architecture

Descricao: |
  Criar e manter documentação técnica abrangente.
  
  Tópicos:
  - Arquitetura: ES + PGV + WRF (diagrama de fluxo)
  - Pipeline de busca completo (step by step)
  - Parâmetros: quais são, como ajustá-los, valores padrão
  - Elasticsearch: qual texto é usado (bruto vs. expandido pela LLM)
  - Prompts: documentar todos os prompts e seus propósitos
  - Troubleshooting: problemas comuns e soluções
  - Ruby/Benedetti Score: documentar fórmula e parametrização

Requisitos Tecnicos:
  Documentação:
    - Formato: Markdown no repositório (docs/)
    - Diagramas: Mermaid.js ou ASCII
    - Versionada junto com código
    - Atualizada a cada mudança significativa no pipeline

DoD:
  - [ ] Documentação acessível (wiki/confluence/repo)
  - [ ] Diagramas de arquitetura
  - [ ] Todos os parâmetros documentados
  - [ ] Guia de troubleshooting

Criterios de Aceitacao:
  - [ ] Pipeline documentado step-by-step
  - [ ] Parâmetros com valores padrão e ranges
  - [ ] Troubleshooting com 10+ problemas comuns
  - [ ] Atualizado com últimas mudanças

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
```

#### Prompt para IA (Cursor/VSCode) — WDT-029

```
CONTEXTO DO PROJETO WEDO TALENT:
- Arquitetura: Elasticsearch + PG Vector + WRF (Weighted Rank Fusion)
- Ambiente: Ruby on Rails + Python FastAPI

---

TAREFA: Criar documentação técnica completa do sistema de busca.

TÓPICOS OBRIGATÓRIOS:

1. docs/search/ARCHITECTURE.md
   - Diagrama do pipeline completo (Mermaid)
   - Fluxo: Query → ES + PGV → Filtros estatísticos → WRF → Resultado
   - Componentes e responsabilidades

2. docs/search/PARAMETERS.md
   - Tabela de todos os parâmetros ajustáveis
   - Valores padrão, ranges recomendados, env vars
   - K do WRF, thresholds de score, gap multipliers

3. docs/search/TROUBLESHOOTING.md
   - Resultados irrelevantes: como diagnosticar
   - Performance lenta: checklist
   - Instabilidade de ranking: como detectar e corrigir
   - Discrepância ES vs PGV: o que significa

4. docs/search/PROMPTS.md
   - Todos os prompts LLM usados no pipeline
   - Propósito de cada um
   - Como iterar/versionar prompts
```

---

### CARD WDT-030: Dashboard de Observabilidade do Sistema de Busca

```yaml
Titulo: "[BE/FE] Dashboard de observabilidade do sistema de busca"
Tipo: Story
Sprint: 18
Pontos: 8
Horas: 16
Prioridade: Média
Epic: EPIC-19 (Observabilidade e Documentação de Busca)
Fase: Fase 6 - Docs & Infra
Status: 📋 Pendente Jira
Labels: monitoring, dashboard, ops

Descricao: |
  Dashboard unificado de monitoramento do sistema de busca.
  
  Métricas:
  - Taxa de queda de score por busca
  - Gap semântico médio
  - Estabilidade intra-query
  - Uso de tokens por busca e acumulado
  - Like/dislike ratio por período
  - Tempo de resposta (p50, p95, p99)
  - Candidatos filtrados por etapa do pipeline
  - Distribuição de qualification_level das vagas

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/analytics/search_observability_service.rb
    - Métricas coletadas em cada busca (salvar em search_metrics table)
    - Cache Redis para aggregações
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/SearchObservability.vue
    - ApexCharts para gráficos
    - Auto-refresh a cada 60s

DoD:
  - [ ] Dashboard funcional com todas as métricas
  - [ ] Alertas para anomalias
  - [ ] Histórico de métricas
  - [ ] Filtros por período, tipo de vaga, recrutador

Criterios de Aceitacao:
  - [ ] 8 métricas exibidas
  - [ ] Alerta quando estabilidade < 80%
  - [ ] Alerta quando like_rate < 30%
  - [ ] Histórico de 90 dias
  - [ ] Auto-refresh funcional

Dependencias: WDT-011, WDT-012, WDT-013
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - strategic-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/strategic-dashboard.tsx
  - chart-components.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/charts/chart-components.tsx
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - ConsumptionChart.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/ai-consumption/ConsumptionChart.tsx
```

#### Prompt para IA (Cursor/VSCode) — WDT-030

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3
- Cache: Redis

---

TAREFA: Criar dashboard de observabilidade do sistema de busca.

IMPLEMENTAÇÃO:

Backend:
1. Migration: create_table :search_metrics
   - search_id, es_score_drop_rate, pgv_gap_mean, stability_index,
     tokens_used, response_time_ms, candidates_filtered_es,
     candidates_filtered_pgv, wrf_input_count, wrf_output_count,
     qualification_level, created_at

2. Service: coleta métricas em cada busca (after_action no controller)
3. Aggregação: Redis cache com TTL 60s para dashboard

Frontend:
1. Página com grid de cards:
   - Card 1: Taxa queda média (gauge chart)
   - Card 2: Gap semântico médio (gauge chart)
   - Card 3: Estabilidade (gauge com alerta)
   - Card 4: Tokens/busca (line chart 30 dias)
   - Card 5: Like/dislike ratio (donut chart)
   - Card 6: Tempo resposta p50/p95/p99 (line chart)
   - Card 7: Candidatos filtrados por etapa (funnel chart)
   - Card 8: Distribuição qualification_level (bar chart)

2. Alertas: v-alert type="warning" quando métricas fora do threshold
3. Auto-refresh: setInterval 60s ou vue-use useIntervalFn
```

---

# MAPA DE DEPENDÊNCIAS

## Entre Cards

```
WDT-001 ──→ WDT-002 (FE paginação)
         ──→ WDT-003 (ES exclusão)
         ──→ WDT-004 (PGV exclusão)

WDT-006 ──→ WDT-007 (FE like/dislike)
         ──→ WDT-008 (Dashboard feedback)
         ──→ WDT-027 (Motor aprendizado)
         ──→ WDT-028 (A/B testing)

WDT-009 ──→ WDT-010 (FE classificação)
         ──→ WDT-011 (Taxa queda ES)
         ──→ WDT-012 (Gap semântico PGV)
         ──→ WDT-014 (K dinâmico WRF)

WDT-011 ──→ WDT-015 (Filtro pré-WRF)
WDT-012 ──→ WDT-015 (Filtro pré-WRF)

WDT-016 ──→ WDT-018 (Integração LLM) ✅
         ──→ WDT-021 (Explicit/Implicit/Inferred) ✅
         ──→ WDT-025 (Análise pós-busca)
         ──→ WDT-027 (Motor aprendizado)

WDT-021 ──→ WDT-022 (Score por requisito) ✅
         ──→ WDT-023 (Requisitos excludentes)

# WDT-017, WDT-019, WDT-020 cancelados — sistema auto-evolutivo

WDT-011 ──→ WDT-030 (Dashboard observabilidade)
WDT-012 ──→ WDT-030
WDT-013 ──→ WDT-030
```

## Entre Épicos

```
ÉPICO 3 (MVP) ────→ ÉPICO 16 (Otimização Estatística)
                          │
                          ├──→ ÉPICO 17 (Base de Critérios) ──→ ÉPICO 18 (Aprendizado)
                          │
                          └──→ ÉPICO 19 (Observabilidade)

ÉPICO 3: WDT-006 (like/dislike) ──→ ÉPICO 18: WDT-027 (motor aprendizado)
ÉPICO 16: WDT-009 (classificação) ──→ ÉPICO 17: WDT-016+ (critérios dependem de nível)
```

---

# PRIORIZAÇÃO POR ROI

| Rank | Card(s) | Título | SP | Impacto | Esforço | ROI | Justificativa |
|------|---------|--------|-----|---------|---------|-----|---------------|
| 1 | WDT-001/3/4 | Busca Paginada (backend) | 10 | Altíssimo | Médio | ★★★★★ | Quick win #1. Reduz ~80% custo tokens. |
| 2 | WDT-006/7 | Like/Dislike (API + UI) | 8 | Altíssimo | Baixo | ★★★★★ | Fundamento para TODO aprendizado futuro. |
| 3 | WDT-005 | Remover ordenação ranking | 2 | Alto | Muito Baixo | ★★★★★ | Quick win trivial. Ética e UX. |
| 4 | WDT-002 | Paginação frontend | 3 | Alto | Baixo | ★★★★☆ | Completa experiência de paginação. |
| 5 | WDT-009/10 | Classificação de vaga | 10 | Altíssimo | Alto | ★★★★☆ | BLOQUEANTE para parametrização adaptativa. |
| 6 | WDT-011 | Taxa de queda score (ES) | 5 | Alto | Médio | ★★★★☆ | Elimina irrelevantes do WRF. |
| 7 | WDT-012 | Gap semântico (PGV) | 5 | Alto | Médio | ★★★★☆ | Complementa P4 para embeddings. |
| 8 | WDT-014 | K dinâmico WRF | 5 | Alto | Médio | ★★★☆☆ | WRF mais inteligente. |
| 9 | WDT-016 ✅ | Schema base critérios | 8 | Transformacional | Alto | ★★★★★ | GAME CHANGER. ✅ Implementado (Replit). |
| 10 | WDT-018 ✅ | Critérios + LLM | 8 | Transformacional | Alto | ★★★★☆ | ✅ Implementado (Replit). |
| 11 | WDT-021 ✅ | Explicit/Implicit/Inferred | 5 | Alto | Médio | ★★★★☆ | ✅ Implementado (Replit). |
| 12 | WDT-023 | Requisitos excludentes | 5 | Alto | Baixo | ★★★★☆ | Elimina inadequados antes do WRF. |
| 13 | WDT-029 | Documentação técnica | 8 | Médio | Médio | ★★★☆☆ | Manutenibilidade. Começar early. |
| 14 | WDT-008 | Dashboard feedback | 5 | Médio | Médio | ★★★☆☆ | Visibilidade sobre padrões. |
| 15 | WDT-015 | Filtro pré-WRF combinado | 5 | Alto | Médio | ★★★☆☆ | Orquestra P4+P5. |

---

# CRONOGRAMA POR SPRINT

| Sprint | Cards | SP | Foco |
|--------|-------|----|------|
| **Sprint 1** | WDT-001, 002, 003, 004, 006, 007 | 21 | **MVP: Paginação + Like/Dislike** |
| **Sprint 2** | WDT-005, 008, 029 (início) | 15 | Ordenação, Dashboard feedback, Docs |
| **Sprint 3** | WDT-009, 010 | 10 | Classificação de vaga |
| **Sprint 4** | WDT-011, 012, 013 | 13 | Análise estatística |
| **Sprint 5** | WDT-014, 015 | 10 | WRF otimizado |
| **Sprint 6** | WDT-016 ✅ | 8 | Schema base critérios — ✅ Implementado (Replit) |
| **Sprint 7** | ~~WDT-017~~ ❌ | ~~8~~ | ~~UI admin critérios~~ — ❌ Cancelado |
| **Sprint 8** | WDT-018 ✅ | 8 | Integração critérios + LLM — ✅ Implementado (Replit) |
| **Sprint 9** | ~~WDT-019, 020~~ ❌ | ~~18~~ | ~~Dashboard critérios + workshops~~ — ❌ Cancelados |
| **Sprint 10** | WDT-021 ✅ | 5 | Explicit/Implicit/Inferred — ✅ Implementado (Replit) |
| **Sprint 11** | WDT-022 ✅ | 5 | Score por requisito — ✅ Implementado (Replit) |
| **Sprint 12** | WDT-023 | 5 | Requisitos excludentes |
| **Sprint 13** | WDT-024, 025 | 13 | Enriquecimento + análise pós-busca |
| **Sprint 14** | WDT-026 | 3 | Flags inconsistência |
| **Sprint 15-16** | WDT-027 | 13 | Motor de aprendizado |
| **Sprint 17** | WDT-028 | 8 | A/B testing |
| **Sprint 18** | WDT-029 (final), 030 | 16 | Docs + Observabilidade |
