# DOCUMENTACAO DE FLUXOS - FUNIL DE TALENTOS

> **Versao:** 2.0  
> **Data:** Dezembro 2024 (Atualizado)  
> **Modulo:** Funil de Talentos  
> **Objetivo:** Documentacao orientada a fluxos para desenvolvimento

---

## CHANGELOG v2.0 (Dezembro 2024)

### Novas Funcionalidades Implementadas

1. **Integracao Pearch AI Completa**
   - API Key configurada via secrets (`PEARCH_API_KEY`)
   - Busca híbrida funcionando (local + global 800M+ perfis)
   - Sistema de créditos com estimativa antes da busca
   - Importação de candidatos para staging table

2. **SearchSpec - Filtros Estruturados**
   - Parsing inteligente de query para filtros
   - Suporte a location, skills, seniority, industries
   - Filtros de empresa: funding_stages, company_hq_countries, company_tags
   - Filtros de formação: institution_tiers, institution_countries, institution_ranking

3. **Novos Componentes de Filtros Avançados**
   - CompanyFilterInput, CompanyHQLocationsInput
   - FundingStagesInput, CompanyTagsInput
   - UniversitiesFilterInput, UniversityLocationsInput
   - IndustryFilterInput, LanguageFilterInput
   - TimezoneDropdown, RadiusDropdown
   - ExcludedCompaniesInput, ExcludedUniversitiesInput

4. **Sistema de Tabs Reorganizado**
   - favorites-tab.tsx - Candidatos favoritos
   - lists-tab.tsx - Gestão de listas
   - history-tab.tsx - Histórico de buscas
   - saved-searches-tab.tsx - Buscas salvas
   - pipelines-tab.tsx - Pipelines de recrutamento
   - personas-tab.tsx - Arquetipos de candidatos
   - mapping-tab.tsx - Mapeamento de mercado

5. **Staging Table para Candidatos Externos**
   - Candidatos descobertos ficam em `external_candidate_profiles`
   - Promoção explícita para base principal via `/candidates/promote/{id}`
   - Evita poluição da base com candidatos sem contato revelado

6. **Melhorias de UX**
   - Credit confirmation dialog antes de busca global
   - Smart search input com autocomplete
   - Preview lateral com navegação por setas
   - Contextual actions banner para ações em lote

---

## INDICE DE FLUXOS

1. [FLUXO 01: Busca de Candidatos](#fluxo-01-busca-de-candidatos)
2. [FLUXO 02: Gestao de Favoritos](#fluxo-02-gestao-de-favoritos)
3. [FLUXO 03: Gestao de Listas](#fluxo-03-gestao-de-listas)
4. [FLUXO 04: Historico e Reutilizacao](#fluxo-04-historico-e-reutilizacao)
5. [FLUXO 05: Busca Global Pearch](#fluxo-05-busca-global-pearch)
6. [FLUXO 06: Vinculacao a Vagas](#fluxo-06-vinculacao-a-vagas)
7. [FLUXO 07: Comunicacao com Candidatos](#fluxo-07-comunicacao-com-candidatos)

---

# FLUXO 01: BUSCA DE CANDIDATOS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Busca de Candidatos com IA**

### O que esse fluxo entrega
Sistema de busca inteligente que permite encontrar candidatos usando linguagem natural, perfis similares, job descriptions, queries booleanas ou arquetipos de personalidade.

### Para qual usuario
- Recrutador (usuario principal)
- Tech Recruiter
- Headhunter
- Gestor de RH

### Resultado final esperado
Lista de candidatos rankeados por relevancia/score, prontos para serem adicionados a listas, favoritos ou vagas.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Pagina/Componente | Descricao | Arquivo |
|-------------------|-----------|---------|
| CandidatesPage | Pagina principal do Funil | candidates-page.tsx |
| SearchTab | Tab ativa de busca | search-tab.tsx |
| SmartSearchInput | Input AI-powered | smart-search-input.tsx |
| ContextPills | Pills de entidades | context-pills.tsx |
| SourceSelector | Toggle Local/Global/Hibrido | source-selector.tsx |
| AdvancedFiltersModal | Modal de filtros | advanced-filters-modal.tsx |
| UnifiedCandidateTable | Tabela de resultados | unified-candidate-table.tsx |
| CandidatePreview | Painel lateral | candidate-preview.tsx |
| ContextualActionsBanner | Banner de acoes | contextual-actions-banner.tsx |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/search/candidates | POST | Busca híbrida (local + Pearch) |
| /api/v1/search/candidates/import | POST | Importar candidatos Pearch para staging |
| /api/v1/candidates/promote/{id} | POST | Promover candidato de staging para base |
| /api/v1/search/parse-query | POST | Parsing de query para SearchSpec |
| /api/v1/search/analyze | POST | Análise pós-busca com LIA |
| /api/v1/search-assistant/autocomplete | GET | Autocomplete de busca |
| /api/v1/search-assistant/analyze | POST | Análise de query |
| /api/v1/enhance-prompt | POST | Enhancement de prompt com IA |
| /api/v1/candidates/{id} | GET | Detalhe do candidato |
| /api/v1/candidates/favorites | GET/POST | Gestão de favoritos |
| /api/v1/candidates/viewed | GET | Candidatos visualizados |
| /api/v1/candidates/hidden | GET | Candidatos ocultos |
| /api/v1/candidate-lists | GET/POST | Gestão de listas |
| /api/v1/company/global-search-settings | GET | Configurações globais de busca |

### Dados

| Tabela | Descricao |
|--------|-----------|
| candidates | Candidatos da base local (promovidos) |
| external_candidate_profiles | Staging table - candidatos descobertos via Pearch |
| candidate_skills | Skills por candidato |
| candidate_experiences | Experiências com dados de empresa |
| candidate_education | Formação com dados de instituição |
| candidate_favorites | Favoritos por usuário |
| candidate_lists | Listas de candidatos |
| candidate_list_items | Itens das listas |
| search_history | Histórico de buscas |
| saved_searches | Buscas salvas |

### IA

| Componente | Modelo | Funcao |
|------------|--------|--------|
| Entity Extraction | Claude Sonnet | Extrair entidades da query |
| Semantic Search | Embeddings | Busca semantica |
| Score Calculation | Claude Sonnet | Calcular relevancia |
| JD Parsing | Claude Sonnet | Extrair requisitos de JD |

### Integracoes Externas

| Servico | Uso | Status |
|---------|-----|--------|
| Pearch AI | Busca global (800M+ perfis) | ✅ Implementado |
| Anthropic Claude | Entity extraction, scoring, análise | ✅ Implementado |
| Google Gemini | Voice-to-text, fallback AI | ✅ Implementado |

### Configuracao Pearch (OBRIGATÓRIO)

Para a busca híbrida funcionar, é necessário configurar:

```
PEARCH_API_KEY=<sua-api-key-pearch>
```

Sem esta configuração, apenas a busca local funcionará.

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| BUS-F01 | Digitar Query Natural | Usuario digita texto em linguagem natural |
| BUS-F02 | Extrair Entidades | LIA extrai skills, localizacao, experiencia |
| BUS-F03 | Exibir Context Pills | Mostrar entidades como pills editaveis |
| BUS-F04 | Editar Pills | Usuario pode remover ou editar pills |
| BUS-F05 | Selecionar Modo | Escolher: Natural, Similar, JD, Boolean, Arquetipo |
| BUS-F06 | Selecionar Fonte | Escolher: Local, Global, Hibrido |
| BUS-F07 | Aplicar Filtros | Abrir modal de filtros avancados |
| BUS-F08 | Executar Busca | Disparar busca com parametros |
| BUS-F09 | Exibir Loading | Mostrar estado de carregamento |
| BUS-F10 | Exibir Resultados | Renderizar tabela de candidatos |
| BUS-F11 | Ordenar Resultados | Ordenar por coluna clicada |
| BUS-F12 | Paginar Resultados | Navegar entre paginas |
| BUS-F13 | Selecionar Candidatos | Checkbox para selecao multipla |
| BUS-F14 | Abrir Preview | Clique abre painel lateral |
| BUS-F15 | Navegar no Preview | Setas para proximo/anterior |
| BUS-F16 | Abrir Perfil Completo | Maximizar para modal fullscreen |
| BUS-F17 | Salvar Busca | Salvar query atual como favorita |
| BUS-F18 | Ver Insights LIA | Painel com sugestoes da IA |
| BUS-F19 | Refinar Busca | Aplicar sugestoes de refinamento |
| BUS-F20 | Salvar no Historico | Automatico apos cada busca |

---

## 4. Documentacao Detalhada (por funcionalidade)

---

### BUS-F01: Digitar Query Natural

#### Historia de Usuario
"Como recrutador, eu quero digitar uma busca em linguagem natural para encontrar candidatos sem precisar construir queries complexas."

#### Regras de Negocio
1. Input aceita texto livre em portugues ou ingles
2. Minimo de 3 caracteres para iniciar sugestoes
3. Maximo de 500 caracteres
4. Debounce de 300ms antes de processar
5. Sugestoes de autocomplete baseadas em historico

#### Formulas e Logicas
```
Se tamanho(query) >= 3:
  Chamar autocomplete API
  Exibir sugestoes do historico
  
Se tecla == Enter OU clique em Buscar:
  Chamar entity extraction
  Disparar busca
```

#### Inputs
- Texto livre (string)
- Modo selecionado (enum)
- Fonte selecionada (enum)

#### Outputs
- Entidades extraidas (objeto)
- Query processada (string)

#### Validacoes
- Query nao pode ser vazia
- Query deve ter >= 3 caracteres
- Caracteres especiais sanitizados

#### Edge Cases
- Query muito curta: exibir dica
- Query muito longa: truncar em 500
- Query so com espacos: ignorar
- Query com emojis: remover emojis

---

### BUS-F02: Extrair Entidades

#### Historia de Usuario
"Como sistema, eu preciso extrair entidades da query para realizar busca semantica precisa."

#### Regras de Negocio
1. Identificar skills tecnicas (Python, React, etc)
2. Identificar localizacao (SP, Sao Paulo, Brasil)
3. Identificar experiencia (5 anos, senior, junior)
4. Identificar cargo (desenvolvedor, gerente)
5. Identificar modelo de trabalho (remoto, hibrido)
6. Retornar confianca por entidade (0-1)

#### Formulas e Logicas
```
PROMPT Claude:
"Extraia as seguintes entidades da query de busca de candidatos:
- skills: lista de habilidades tecnicas
- location: cidade, estado ou pais
- experience_years: numero de anos
- seniority: junior, pleno, senior, especialista
- job_title: cargo ou funcao
- work_model: remoto, hibrido, presencial

Query: {query}

Retorne JSON com confidence score (0-1) para cada campo."
```

#### Inputs
- Query texto (string)
- Modo de busca (enum)
- Idioma preferido (string)

#### Outputs
```json
{
  "skills": [{"name": "Python", "confidence": 0.95}],
  "location": {"city": "Sao Paulo", "state": "SP", "confidence": 0.9},
  "experience_years": {"min": 5, "confidence": 0.8},
  "seniority": {"level": "senior", "confidence": 0.85},
  "job_title": {"title": "Desenvolvedor", "confidence": 0.7},
  "work_model": null
}
```

#### Validacoes
- Timeout de 10 segundos
- Se IA falhar, usar busca textual
- Confianca < 0.5 nao exibir pill

#### Edge Cases
- IA timeout: fallback para busca textual
- IA retorna erro: logar e continuar com busca simples
- Entidades ambiguas: exibir todas com baixa confianca

---

### BUS-F08: Executar Busca

#### Historia de Usuario
"Como recrutador, eu quero executar a busca e ver resultados relevantes ordenados por match."

#### Regras de Negocio
1. Combinar entidades + filtros em query
2. Buscar na fonte selecionada (Local/Global/Hibrido)
3. Calcular score de match para cada candidato
4. Ordenar por score decrescente
5. Paginar em 50 items por pagina (default)
6. Salvar busca no historico automaticamente
7. Cache de 5 minutos para mesma query

#### Formulas e Logicas
```
Score = (
  skill_match * 0.40 +
  experience_match * 0.25 +
  location_match * 0.15 +
  seniority_match * 0.10 +
  recency_bonus * 0.10
)

skill_match = skills_encontradas / skills_buscadas
experience_match = min(1, exp_candidato / exp_requisitada)
location_match = 1 se match, 0.5 se mesmo estado, 0 se nao
seniority_match = 1 se exato, 0.5 se adjacente, 0 se distante
recency_bonus = 1 - (dias_desde_atualizacao / 365)
```

#### Inputs
```json
{
  "query": "Desenvolvedor Python SP",
  "mode": "natural",
  "source": "local",
  "entities": {...},
  "filters": {...},
  "page": 1,
  "per_page": 50,
  "sort_by": "score",
  "sort_order": "desc"
}
```

#### Outputs
```json
{
  "candidates": [...],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "total_pages": 3,
  "search_id": "uuid",
  "cached": false,
  "execution_time_ms": 450
}
```

#### Validacoes
- Autenticacao obrigatoria
- Rate limit: 10 req/min
- company_id obrigatorio (multi-tenant)

#### Edge Cases
- 0 resultados: sugerir expansao ou refinamento
- Timeout: retornar resultados parciais
- Erro de conexao: retry com backoff

---

## 5. Cards de Especificacao (Estilo Jira)

---

### CARD BUS-FLOW-001: Fluxo Completo de Busca Natural

```yaml
Titulo: [FULL-STACK] Implementar Fluxo Completo de Busca Natural
Tipo: Epic
Sprint: 1-2
Pontos: 34

Descricao: |
  Implementar o fluxo completo de busca de candidatos usando
  linguagem natural, desde o input ate a exibicao de resultados.

Historia de Usuario: |
  Como recrutador, eu quero buscar candidatos usando linguagem
  natural e ver resultados relevantes em uma tabela organizada.

Regras de Negocio:
  1. Input aceita texto livre
  2. LIA extrai entidades automaticamente
  3. Entidades exibidas como pills editaveis
  4. Resultados ordenados por score de match
  5. Historico salvo automaticamente
  6. Cache de 5 minutos

Requisitos Tecnicos:
  Frontend:
    - SmartSearchInput com debounce 300ms
    - ContextPills editaveis
    - SourceSelector (Local/Global/Hibrido)
    - UnifiedCandidateTable com virtualizacao
    - CandidatePreview redimensionavel
    - Loading skeleton durante busca
  Backend:
    - POST /api/v1/candidates/search
    - Entity extraction com Claude
    - Score calculation
    - Cache com Redis
    - Rate limiting
  Dados:
    - candidates (indexados por skills, location)
    - search_history (auto-save)
  IA:
    - Prompt de entity extraction
    - Fallback para busca textual
    - Timeout de 10s

Integracoes:
  - Claude API (entity extraction)
  - Pearch API (se fonte global)

Riscos:
  - Latencia IA > 3s: usar streaming/skeleton
  - Custo API: cache agressivo
  - Precisao extracao: pills editaveis

DoD:
  - [ ] Input funciona com debounce
  - [ ] Entidades extraidas e exibidas
  - [ ] Pills editaveis
  - [ ] Busca retorna resultados
  - [ ] Tabela renderiza com paginacao
  - [ ] Preview abre ao clicar
  - [ ] Historico salvo
  - [ ] Testes unitarios passando
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] "Dev Python SP" retorna devs Python em SP
  - [ ] Pills skill=Python, location=SP aparecem
  - [ ] Tempo < 5s para 100 resultados
  - [ ] Selecionar candidato abre preview
  - [ ] Busca aparece no historico
```

---

### CARD BUS-FLOW-002: Sistema de Filtros Avancados

```yaml
Titulo: [FRONTEND] Implementar Sistema de Filtros Avancados
Tipo: Feature
Sprint: 2
Pontos: 8

Descricao: |
  Modal com filtros avancados para refinar resultados de busca
  com multiplos criterios combinaveis.

Historia de Usuario: |
  Como recrutador, eu quero aplicar filtros avancados para
  encontrar candidatos mais especificos para minha vaga.

Regras de Negocio:
  1. Filtro por localizacao (autocomplete cidades)
  2. Filtro por experiencia (slider 0-30 anos)
  3. Filtro por senioridade (multi-select)
  4. Filtro por modelo de trabalho (multi-select)
  5. Filtro por faixa salarial (range input)
  6. Filtro por skills (autocomplete multi)
  7. Filtro por idiomas (multi-select)
  8. Filtros combinaveis com AND
  9. Contador de filtros ativos
  10. Limpar todos os filtros

Requisitos Tecnicos:
  Frontend:
    - AdvancedFiltersModal
    - Autocomplete para localizacao
    - Slider para experiencia
    - Multi-select para senioridade
    - Range input para salario
    - Tags input para skills
    - Badge contador
    - Botao limpar

DoD:
  - [ ] Modal abre e fecha
  - [ ] Todos os filtros funcionam
  - [ ] Filtros sao combinaveis
  - [ ] Contador atualiza
  - [ ] Limpar reseta todos
  - [ ] Filtros persistem na sessao

Criterios de Aceitacao:
  - [ ] Filtrar por SP + Senior funciona
  - [ ] Limpar remove todos os filtros
  - [ ] Badge mostra "3 filtros"
```

---

## 6. Diagrama da Jornada do Fluxo

### Jornada do Usuario

```
INICIO
  |
  v
[Usuario acessa Funil de Talentos]
  |
  v
[Tab Busca esta ativa por padrao]
  |
  v
[Usuario digita query no input]
  |
  +-- Ex: "Desenvolvedor React 5 anos SP remoto"
  |
  v
[Sistema exibe loading durante extracao]
  |
  v
[Pills aparecem: React | 5 anos | SP | Remoto]
  |
  +-- Usuario pode editar/remover pills
  |
  v
[Usuario seleciona fonte: Local]
  |
  v
[Usuario clica em "Buscar" ou Enter]
  |
  v
[Loading na tabela]
  |
  v
[Resultados aparecem ordenados por score]
  |
  +-- 85 candidatos encontrados
  |
  v
[Usuario clica em candidato da linha 3]
  |
  v
[Preview abre na lateral]
  |
  +-- Nome, cargo, skills, score
  |
  v
[Usuario navega com setas UP/DOWN]
  |
  v
[Usuario decide favoritar candidato]
  |
  v
[Clica na estrela no preview]
  |
  v
[Toast: "Candidato adicionado aos favoritos"]
  |
  v
[Usuario seleciona 5 candidatos (checkbox)]
  |
  v
[Banner de acoes aparece no topo]
  |
  v
[Usuario clica em "Adicionar a Lista"]
  |
  v
[Modal de listas abre]
  |
  v
[Usuario seleciona "Projeto Alpha"]
  |
  v
[Toast: "5 candidatos adicionados a Projeto Alpha"]
  |
FIM
```

### Jornada do Sistema

```
[FRONT] Usuario digita query no SmartSearchInput
    |
    v
[FRONT] Debounce de 300ms
    |
    v
[FRONT] Chama API de entity extraction
    |
    v
[BACK] POST /api/v1/nlp/extract-entities
    |
    v
[IA] Claude processa query com prompt template
    |
    v
[IA] Retorna JSON: {skills: ["React"], experience: 5, location: "SP"}
    |
    v
[BACK] Retorna entidades para frontend
    |
    v
[FRONT] Renderiza ContextPills
    |
    v
[FRONT] Usuario confirma e clica Buscar
    |
    v
[FRONT] Monta payload com entities + filters + source
    |
    v
[FRONT] POST /api/v1/candidates/search com loading state
    |
    v
[BACK] Recebe request autenticado
    |
    v
[BACK] Valida company_id (multi-tenant)
    |
    v
[BACK] Verifica cache Redis
    |
    +-- Cache hit? Retorna cached
    |
    v
[BACK] Monta query SQL/ElasticSearch
    |
    v
[DADOS] SELECT * FROM candidates WHERE skills && ARRAY['React'] AND location = 'SP'...
    |
    v
[BACK] Para cada candidato, calcula score
    |
    v
[BACK] Ordena por score DESC
    |
    v
[BACK] Pagina resultados
    |
    v
[BACK] Salva no cache Redis (TTL 5min)
    |
    v
[DADOS] INSERT INTO search_history (query, entities, results_count, ...)
    |
    v
[BACK] Retorna JSON com candidates[], total, pages
    |
    v
[FRONT] Recebe response
    |
    v
[FRONT] Atualiza estado com candidatos
    |
    v
[FRONT] Renderiza UnifiedCandidateTable
    |
    v
[FRONT] Usuario clica em linha
    |
    v
[FRONT] Abre CandidatePreview com dados do candidato
    |
    v
[FRONT] Usuario clica em favoritar
    |
    v
[FRONT] POST /api/v1/candidates/{id}/favorite
    |
    v
[BACK] INSERT INTO candidate_favorites
    |
    v
[FRONT] Atualiza UI optimisticamente
    |
FIM
```

---

## 7. Roadmap do Fluxo em Fases

### Fase 1: MVP Busca (Sprint 1)
```
[SmartSearchInput basico]
         |
         v
[Entity Extraction simples]
         |
         v
[Busca Local apenas]
         |
         v
[UnifiedCandidateTable basica]
         |
         v
[Paginacao simples]

Dependencias: Nenhuma
Entregaveis:
  - Input de busca funcional
  - Extracao de skills e localizacao
  - Tabela com resultados
  - Paginacao
```

### Fase 2: Interacao Rica (Sprint 2)
```
[Context Pills editaveis]
         |
         v
[Filtros Avancados]
         |
         v
[CandidatePreview lateral]
         |
         v
[Selecao multipla + Banner]
         |
         v
[Historico automatico]

Dependencias: Fase 1 completa
Entregaveis:
  - Pills com edicao
  - Modal de filtros
  - Preview redimensionavel
  - Acoes em lote
  - Historico salvo
```

### Fase 3: Modos Avancados (Sprint 3)
```
[Busca por Perfil Similar]
         |
         v
[Busca por Job Description]
         |
         v
[Busca Boolean]
         |
         v
[Busca por Arquetipos]

Dependencias: Fase 2 completa
Entregaveis:
  - Input de URL/candidato
  - Textarea de JD
  - Parser boolean
  - Grid de arquetipos
```

### Fase 4: Busca Global (Sprint 4)
```
[Integracao Pearch]
         |
         v
[Confirmacao de Creditos]
         |
         v
[Revelacao de Contatos]
         |
         v
[Salvamento Local]

Dependencias: Fase 2 completa + Contrato Pearch
Entregaveis:
  - Toggle de fonte
  - Dialog de creditos
  - Revelar email/telefone
  - Persistir candidato
```

---

## 8. Lista de Tasks Importaveis

```csv
ID,Titulo,Descricao,Tipo,Dependencias,DoD,Est Ideal,Est Real,Est Pess
BUS-F01-T1,[FRONT] SmartSearchInput Base,Input com debounce e placeholder,feature,,Input renderiza e dispara eventos,3h,5h,8h
BUS-F01-T2,[FRONT] Autocomplete Historico,Sugestoes baseadas em buscas anteriores,feature,BUS-F01-T1,Sugestoes aparecem ao digitar,2h,4h,6h
BUS-F02-T1,[BACK] Endpoint Entity Extraction,POST /api/v1/nlp/extract-entities,feature,,API extrai entidades,4h,6h,10h
BUS-F02-T2,[IA] Prompt Template Extraction,Prompt para Claude extrair entidades,feature,,Prompt retorna JSON correto,2h,3h,5h
BUS-F03-T1,[FRONT] ContextPills Component,Pills com icone e close button,feature,BUS-F02-T1,Pills renderizam,3h,5h,8h
BUS-F04-T1,[FRONT] Edicao de Pills,Inline edit ao clicar na pill,feature,BUS-F03-T1,Pill editavel,2h,4h,6h
BUS-F05-T1,[FRONT] ModeSelector Component,Tabs para modos de busca,feature,,Toggle funciona,2h,3h,5h
BUS-F06-T1,[FRONT] SourceSelector Component,Toggle Local/Global/Hibrido,feature,,Fonte persistida,2h,3h,5h
BUS-F07-T1,[FRONT] AdvancedFiltersModal,Modal com todos filtros,feature,,Modal funcional,6h,10h,16h
BUS-F08-T1,[BACK] Endpoint Search Principal,POST /api/v1/candidates/search,feature,BUS-F02-T1,API retorna candidatos,6h,10h,16h
BUS-F08-T2,[BACK] Score Calculation,Algoritmo de scoring,feature,BUS-F08-T1,Scores calculados,4h,6h,10h
BUS-F08-T3,[BACK] Cache Redis,Cache de resultados 5min,feature,BUS-F08-T1,Cache funciona,2h,4h,6h
BUS-F09-T1,[FRONT] Loading Skeleton,Skeleton animado na tabela,feature,,Skeleton renderiza,2h,3h,5h
BUS-F10-T1,[FRONT] UnifiedCandidateTable,Tabela configuravel,feature,BUS-F08-T1,Tabela renderiza,8h,12h,20h
BUS-F11-T1,[FRONT] Ordenacao Colunas,Sort ao clicar header,feature,BUS-F10-T1,Ordenacao funciona,2h,3h,5h
BUS-F12-T1,[FRONT] Paginacao,Navegacao entre paginas,feature,BUS-F10-T1,Paginacao funciona,2h,3h,5h
BUS-F13-T1,[FRONT] Selecao Multipla,Checkbox com contador,feature,BUS-F10-T1,Selecao funciona,3h,5h,8h
BUS-F14-T1,[FRONT] CandidatePreview,Painel lateral,feature,BUS-F10-T1,Preview abre,6h,10h,16h
BUS-F15-T1,[FRONT] Navegacao Preview,Setas up/down,feature,BUS-F14-T1,Navegacao funciona,2h,3h,5h
BUS-F16-T1,[FRONT] CandidatePage Modal,Modal fullscreen,feature,BUS-F14-T1,Modal funciona,8h,12h,20h
BUS-F17-T1,[FRONT] Salvar Busca Button,Botao com modal,feature,,Modal funciona,3h,5h,8h
BUS-F17-T2,[BACK] API Saved Searches,CRUD buscas salvas,feature,,API funciona,4h,6h,10h
BUS-F18-T1,[FRONT] LIA Insights Panel,Painel com sugestoes,feature,,Painel funciona,4h,6h,10h
BUS-F20-T1,[BACK] Auto-save Historico,Salvar busca automaticamente,feature,BUS-F08-T1,Historico salvo,2h,3h,5h
```

---

## 9. Padrao de Design do Fluxo

### Componentes Necessarios

| Componente | Vuetify 3 | Funcao |
|------------|-----------|--------|
| v-text-field | Input | SmartSearchInput |
| v-chip | Pill | ContextPills |
| v-btn-toggle | Toggle | ModeSelector |
| v-btn-toggle | Toggle | SourceSelector |
| v-dialog | Modal | AdvancedFiltersModal |
| v-data-table | Tabela | UnifiedCandidateTable |
| v-navigation-drawer | Drawer | CandidatePreview |
| v-skeleton-loader | Loading | Skeleton states |
| v-pagination | Paginacao | Pagination |
| v-checkbox | Checkbox | Selecao |
| v-banner | Banner | ContextualActionsBanner |

### Paleta de Cores

```css
/* Cores principais */
--color-primary: #60BED1;      /* Accent - acoes principais */
--color-bg-card: #FFFFFF;       /* Fundo de cards */
--color-bg-page: #F9FAFB;       /* Fundo da pagina */
--color-border: #E5E7EB;        /* Bordas (gray-200) */
--color-border-light: #F3F4F6;  /* Bordas leves (gray-100) */

/* Texto */
--color-text-primary: #111827;   /* Titulos (gray-900) */
--color-text-secondary: #4B5563; /* Corpo (gray-600) */
--color-text-muted: #9CA3AF;     /* Hints (gray-400) */

/* Status */
--color-success: #10B981;
--color-warning: #F59E0B;
--color-error: #EF4444;
--color-info: #3B82F6;
```

### Tokens de Tipografia

```css
/* Titulos - Source Serif 4 */
.title-large { font: 600 20px/28px 'Source Serif 4'; }
.title { font: 600 16px/24px 'Source Serif 4'; }

/* Corpo - Open Sans */
.body { font: 400 14px/20px 'Open Sans'; }
.body-small { font: 400 12px/16px 'Open Sans'; }
.caption { font: 400 11px/14px 'Open Sans'; color: var(--color-text-muted); }
.label { font: 500 12px/16px 'Open Sans'; text-transform: uppercase; }
```

### Tailwind (Prototipo React)

```jsx
// SmartSearchInput
<div className="relative">
  <input 
    className="w-full px-4 py-3 border border-gray-200 rounded-lg 
               focus:ring-2 focus:ring-primary/20 focus:border-primary
               text-sm text-gray-800 placeholder-gray-400"
    placeholder="Buscar candidatos..."
  />
  <div className="absolute right-3 top-1/2 -translate-y-1/2">
    <Search className="w-5 h-5 text-gray-400" />
  </div>
</div>

// ContextPill
<span className="inline-flex items-center gap-1.5 px-3 py-1 
                 bg-primary/10 text-primary rounded-full text-sm">
  <span>{label}</span>
  <button className="hover:bg-primary/20 rounded-full p-0.5">
    <X className="w-3 h-3" />
  </button>
</span>

// Tabela
<table className="w-full">
  <thead className="bg-gray-50 border-b border-gray-100">
    <tr>
      <th className="px-4 py-3 text-left text-xs font-medium 
                     text-gray-500 uppercase tracking-wider">
        Nome
      </th>
    </tr>
  </thead>
  <tbody className="divide-y divide-gray-100">
    <tr className="hover:bg-gray-50 cursor-pointer">
      <td className="px-4 py-4 text-sm text-gray-800">
        Joao Silva
      </td>
    </tr>
  </tbody>
</table>
```

### Vuetify 3 (Produto Final)

```vue
<!-- SmartSearchInput -->
<v-text-field
  v-model="query"
  variant="outlined"
  density="comfortable"
  placeholder="Buscar candidatos..."
  prepend-inner-icon="mdi-magnify"
  class="search-input"
  hide-details
/>

<!-- ContextPill -->
<v-chip
  closable
  color="primary"
  variant="tonal"
  size="small"
  @click:close="removePill"
>
  {{ label }}
</v-chip>

<!-- Tabela -->
<v-data-table
  :headers="headers"
  :items="candidates"
  :loading="loading"
  hover
  class="elevation-0"
>
  <template #item.name="{ item }">
    <div class="d-flex align-center gap-3">
      <v-avatar size="32">
        <v-img :src="item.avatar" />
      </v-avatar>
      <span class="text-body-2">{{ item.name }}</span>
    </div>
  </template>
</v-data-table>

<!-- Preview Drawer -->
<v-navigation-drawer
  v-model="previewOpen"
  location="right"
  width="400"
  temporary
>
  <CandidatePreview :candidate="selectedCandidate" />
</v-navigation-drawer>
```

---

## 10. Uso de IA no Fluxo

### Onde Entra a IA

| Ponto | Trigger | Modelo |
|-------|---------|--------|
| Entity Extraction | Usuario digita query | Claude Sonnet |
| Semantic Search | Busca executada | Embeddings |
| Score Calculation | Resultados retornados | Claude (opcional) |
| JD Parsing | Usuario cola JD | Claude Sonnet |
| Sugestoes Refinamento | Poucos resultados | Claude Sonnet |
| Archetype Generation | Usuario descreve perfil | Claude Sonnet |

### Como Processa

#### Entity Extraction
```
INPUT: "Desenvolvedor Python senior 5 anos SP remoto"

PROMPT:
"""
Voce e um assistente especializado em recrutamento.
Extraia as seguintes entidades da query de busca:

{
  "skills": lista de habilidades tecnicas,
  "location": {cidade, estado, pais},
  "experience_years": numero minimo de anos,
  "seniority": junior|pleno|senior|especialista,
  "job_title": cargo ou funcao,
  "work_model": remoto|hibrido|presencial,
  "salary_range": {min, max, currency} se mencionado
}

Para cada campo, inclua um "confidence" de 0 a 1.
Retorne apenas JSON valido.

Query: {query}
"""

OUTPUT:
{
  "skills": [{"name": "Python", "confidence": 0.95}],
  "location": {"city": "Sao Paulo", "state": "SP", "confidence": 0.9},
  "experience_years": {"min": 5, "confidence": 0.85},
  "seniority": {"level": "senior", "confidence": 0.9},
  "job_title": {"title": "Desenvolvedor", "confidence": 0.8},
  "work_model": {"model": "remoto", "confidence": 0.95}
}
```

#### JD Parsing
```
INPUT: Job Description completa (texto longo)

PROMPT:
"""
Analise esta descricao de vaga e extraia:

{
  "required_skills": [lista de skills obrigatorias],
  "nice_to_have_skills": [lista de diferenciais],
  "experience_years": numero minimo,
  "seniority": nivel esperado,
  "responsibilities": [principais responsabilidades],
  "benefits": [beneficios mencionados],
  "salary_range": {min, max} se informado,
  "work_model": remoto|hibrido|presencial
}

Job Description:
{jd_text}
"""

OUTPUT: JSON estruturado para matching
```

### Riscos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Latencia > 5s | Media | Alto | Streaming, skeleton, cache |
| Custo alto por query | Alta | Medio | Cache agressivo, batch |
| Extracao incorreta | Media | Medio | Pills editaveis, confirmacao |
| Hallucination | Baixa | Alto | Validacao de schema JSON |
| Timeout | Baixa | Alto | Retry, fallback textual |

### Fallbacks

```yaml
Se Claude timeout (>10s):
  1. Logar erro com request_id
  2. Usar busca textual simples (LIKE '%query%')
  3. Exibir aviso: "Busca simplificada - tente novamente"
  4. Oferecer retry button

Se entity extraction falhar:
  1. Usar query completa como skill match
  2. Nao exibir pills
  3. Sugerir modo Boolean

Se score calculation falhar:
  1. Usar score baseado apenas em matches exatos
  2. Ordenar por data de atualizacao

Se Pearch nao responder:
  1. Mostrar apenas resultados locais
  2. Banner: "Busca global indisponivel"
  3. Botao: "Tentar novamente"
```

---

# FLUXO 02: GESTAO DE FAVORITOS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Gestao de Candidatos Favoritos**

### O que esse fluxo entrega
Sistema de favoritos com notas pessoais e pins para priorizar candidatos de interesse do recrutador.

### Para qual usuario
- Recrutador
- Tech Recruiter
- Headhunter

### Resultado final esperado
Lista organizada de candidatos favoritos com notas de contexto e priorizacao por pins.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| FavoritesTab | Tab de favoritos |
| FavoritesList | Lista de favoritos |
| FavoriteCard | Card de candidato favorito |
| NotePopover | Popover para adicionar nota |
| FilterToggle | Toggle Todos/Fixados |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/candidates/favorites | GET | Listar favoritos |
| /api/v1/candidates/{id}/favorite | POST | Favoritar |
| /api/v1/candidates/{id}/favorite | PUT | Atualizar (nota, pin) |
| /api/v1/candidates/{id}/favorite | DELETE | Desfavoritar |

### Dados

| Tabela | Campos |
|--------|--------|
| candidate_favorites | candidate_id, user_id, note, is_pinned, created_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| FAV-F01 | Listar Favoritos | Ver todos os favoritos |
| FAV-F02 | Filtrar por Tipo | Toggle Todos/Fixados |
| FAV-F03 | Buscar Favorito | Busca por nome/cargo |
| FAV-F04 | Favoritar Candidato | Adicionar aos favoritos |
| FAV-F05 | Desfavoritar | Remover dos favoritos |
| FAV-F06 | Fixar Candidato | Pin no topo |
| FAV-F07 | Adicionar Nota | Nota pessoal |
| FAV-F08 | Editar Nota | Atualizar nota |
| FAV-F09 | Ordenar Lista | Por score/nome/data |
| FAV-F10 | Ver Preview | Painel lateral |

---

## 4. Documentacao Detalhada

### FAV-F04: Favoritar Candidato

#### Historia de Usuario
"Como recrutador, eu quero favoritar candidatos para acessa-los rapidamente depois."

#### Regras de Negocio
1. Toggle de favorito (estrela)
2. Animacao visual ao favoritar
3. Sincronizar com backend
4. Fallback para localStorage
5. Candidato aparece na tab Favoritos

#### Inputs
- candidate_id (string)

#### Outputs
- favorite_id (string)
- created_at (timestamp)

#### Validacoes
- Usuario autenticado
- Candidato existe

#### Edge Cases
- Offline: salvar em localStorage, sync depois
- Ja favoritado: ignorar silenciosamente

---

### FAV-F07: Adicionar Nota

#### Historia de Usuario
"Como recrutador, eu quero adicionar notas aos favoritos para lembrar contexto."

#### Regras de Negocio
1. Icone de nota por candidato
2. Popover com textarea
3. Maximo 500 caracteres
4. Salvar ao fechar popover
5. Exibir preview na lista (primeiros 50 chars)

#### Inputs
- candidate_id (string)
- note (string, max 500)

#### Outputs
- updated_at (timestamp)

---

## 5. Cards de Especificacao

### CARD FAV-FLOW-001: Fluxo Completo de Favoritos

```yaml
Titulo: [FULL-STACK] Implementar Fluxo de Favoritos
Tipo: Epic
Sprint: 2
Pontos: 21

Descricao: |
  Sistema completo de favoritos com notas, pins e filtros.

Historia de Usuario: |
  Como recrutador, eu quero marcar candidatos como favoritos
  com notas para organizar meu pipeline pessoal.

Regras de Negocio:
  1. Toggle de favorito (estrela)
  2. Toggle de pin
  3. Notas de ate 500 caracteres
  4. Fixados no topo da lista
  5. Filtro: Todos, Fixados
  6. Ordenacao: Score, Nome, Data

Requisitos Tecnicos:
  Frontend:
    - FavoritesTab
    - Toggle estrela com animacao
    - Toggle pin
    - NotePopover
    - FilterToggle
    - SortDropdown
  Backend:
    - CRUD /api/v1/candidates/{id}/favorite
    - GET /api/v1/candidates/favorites
  Dados:
    - candidate_favorites (note, is_pinned)

DoD:
  - [ ] Favoritar/desfavoritar funciona
  - [ ] Pin funciona
  - [ ] Notas salvam
  - [ ] Filtros funcionam
  - [ ] Ordenacao funciona
  - [ ] Preview funciona

Criterios de Aceitacao:
  - [ ] Estrela toggle favorita
  - [ ] Pin move para o topo
  - [ ] Nota aparece ao hover
  - [ ] Filtrar fixados funciona
```

---

## 6. Diagrama da Jornada do Fluxo

```
INICIO
  |
  v
[Usuario esta na tab Busca]
  |
  v
[Encontra candidato interessante]
  |
  v
[Clica na estrela do candidato]
  |
  v
[FRONT] Toggle estrela com animacao
  |
  v
[BACK] POST /api/v1/candidates/{id}/favorite
  |
  v
[DADOS] INSERT INTO candidate_favorites
  |
  v
[FRONT] Toast: "Adicionado aos favoritos"
  |
  v
[Usuario vai para tab Favoritos]
  |
  v
[Candidato aparece na lista]
  |
  v
[Usuario clica no icone de nota]
  |
  v
[Popover abre com textarea]
  |
  v
[Usuario digita: "Otimo fit para projeto Alpha"]
  |
  v
[Usuario fecha popover]
  |
  v
[BACK] PUT /api/v1/candidates/{id}/favorite {note: "..."}
  |
  v
[Usuario clica no pin]
  |
  v
[Candidato vai para o topo]
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: MVP Favoritos (Sprint 2)
```
[Toggle favoritar]
       |
       v
[Lista de favoritos]
       |
       v
[Desfavoritar]
```

### Fase 2: Enriquecimento (Sprint 2)
```
[Sistema de notas]
       |
       v
[Sistema de pins]
       |
       v
[Filtros e ordenacao]
```

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
FAV-F01-T1,[BACK] API GET Favoritos,feature,3h
FAV-F04-T1,[BACK] API POST Favoritar,feature,2h
FAV-F04-T2,[FRONT] Toggle Estrela,feature,3h
FAV-F05-T1,[BACK] API DELETE Desfavoritar,feature,2h
FAV-F06-T1,[BACK] API PUT Pin,feature,2h
FAV-F06-T2,[FRONT] Toggle Pin,feature,2h
FAV-F07-T1,[FRONT] NotePopover,feature,4h
FAV-F08-T1,[BACK] API PUT Nota,feature,2h
FAV-F09-T1,[FRONT] SortDropdown,feature,2h
FAV-F02-T1,[FRONT] FilterToggle,feature,2h
```

---

## 9. Padrao de Design

### Vuetify 3

```vue
<!-- Toggle Favorito -->
<v-btn
  :icon="isFavorite ? 'mdi-star' : 'mdi-star-outline'"
  :color="isFavorite ? 'amber' : 'grey'"
  variant="text"
  size="small"
  @click="toggleFavorite"
/>

<!-- Toggle Pin -->
<v-btn
  :icon="isPinned ? 'mdi-pin' : 'mdi-pin-outline'"
  :color="isPinned ? 'primary' : 'grey'"
  variant="text"
  size="small"
  @click="togglePin"
/>

<!-- Note Popover -->
<v-menu :close-on-content-click="false">
  <template #activator="{ props }">
    <v-btn v-bind="props" icon="mdi-note-text" variant="text" />
  </template>
  <v-card width="300">
    <v-textarea
      v-model="note"
      placeholder="Adicionar nota..."
      rows="3"
      variant="outlined"
      density="compact"
    />
    <v-card-actions>
      <v-btn size="small" @click="saveNote">Salvar</v-btn>
    </v-card-actions>
  </v-card>
</v-menu>
```

---

## 10. Uso de IA no Fluxo

**Este fluxo NAO utiliza IA diretamente.**

A unica integracao indireta e a exibicao do Score LIA no preview do candidato favorito, que foi calculado anteriormente.

---

# FLUXO 03: GESTAO DE LISTAS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Gestao de Listas de Candidatos**

### O que esse fluxo entrega
Sistema de listas personalizadas para organizar candidatos por projeto, vaga ou criterio.

### Para qual usuario
- Recrutador
- Gestor de RH
- Tech Lead (consultando)

### Resultado final esperado
Candidatos organizados em listas nomeadas e coloridas, vinculaveis a vagas.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| ListsTab | Tab de listas |
| ListGrid | Grid de cards de listas |
| ListCard | Card de uma lista |
| CreateListModal | Modal de criacao |
| ListDetailView | View de detalhe da lista |
| AddToListModal | Modal para adicionar candidatos |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/candidate-lists | GET | Listar listas |
| /api/v1/candidate-lists | POST | Criar lista |
| /api/v1/candidate-lists/{id} | GET | Detalhe da lista |
| /api/v1/candidate-lists/{id} | PUT | Editar lista |
| /api/v1/candidate-lists/{id} | DELETE | Excluir lista |
| /api/v1/candidate-lists/{id}/candidates | POST | Adicionar candidatos |
| /api/v1/candidate-lists/{id}/candidates/{cid} | DELETE | Remover candidato |

### Dados

| Tabela | Campos |
|--------|--------|
| candidate_lists | id, name, description, color, user_id, company_id, created_at |
| candidate_list_items | list_id, candidate_id, added_at |

---

## 3. Lista Completa de Funcionalidades do Fluxo

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| LIS-F01 | Listar Listas | Ver todas as listas |
| LIS-F02 | Criar Lista | Nova lista com nome e cor |
| LIS-F03 | Editar Lista | Alterar nome, descricao, cor |
| LIS-F04 | Excluir Lista | Remover lista (candidatos permanecem) |
| LIS-F05 | Ver Candidatos | Abrir lista e ver membros |
| LIS-F06 | Adicionar Candidato | Incluir candidato na lista |
| LIS-F07 | Remover Candidato | Tirar candidato da lista |
| LIS-F08 | Vincular a Vagas | Adicionar lista inteira a vaga(s) |
| LIS-F09 | Exportar Lista | Download CSV/Excel |
| LIS-F10 | Buscar Listas | Filtrar por nome |

---

## 4. Documentacao Detalhada

### LIS-F02: Criar Lista

#### Historia de Usuario
"Como recrutador, eu quero criar listas para organizar candidatos por projeto."

#### Regras de Negocio
1. Nome obrigatorio (3-50 caracteres)
2. Nome unico por usuario
3. Descricao opcional (max 200 chars)
4. Cor selecionavel (8 opcoes)
5. Limite de 100 listas por usuario

#### Formulas e Logicas
```
cores_disponiveis = [
  "#EF4444", // vermelho
  "#F59E0B", // amarelo
  "#10B981", // verde
  "#3B82F6", // azul
  "#8B5CF6", // roxo
  "#EC4899", // rosa
  "#6B7280", // cinza
  "#60BED1"  // primary
]
```

#### Inputs
```json
{
  "name": "Projeto Alpha",
  "description": "Candidatos para vaga de dev senior",
  "color": "#3B82F6"
}
```

#### Outputs
```json
{
  "id": "uuid",
  "name": "Projeto Alpha",
  "description": "...",
  "color": "#3B82F6",
  "candidates_count": 0,
  "created_at": "2024-12-01T10:00:00Z"
}
```

#### Validacoes
- Nome nao vazio
- Nome unico (case insensitive)
- Cor valida do set
- Limite de listas nao excedido

#### Edge Cases
- Nome duplicado: erro 409 Conflict
- Limite excedido: erro 403 + mensagem clara
- Cor invalida: usar cor default

---

### LIS-F06: Adicionar Candidato a Lista

#### Historia de Usuario
"Como recrutador, eu quero adicionar candidatos a listas para organiza-los."

#### Regras de Negocio
1. Um candidato pode estar em multiplas listas
2. Nao duplicar na mesma lista
3. Adicao em lote (multi-select)
4. Toast de confirmacao

#### Formulas e Logicas
```
Se candidato ja na lista:
  Ignorar silenciosamente
  Contar como sucesso
  
Se limite de candidatos por lista (opcional):
  Bloquear adicao
  Exibir erro
```

#### Inputs
```json
{
  "candidate_ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### Outputs
```json
{
  "added_count": 3,
  "already_in_list": 0,
  "list": {...}
}
```

---

## 5. Cards de Especificacao

### CARD LIS-FLOW-001: CRUD Completo de Listas

```yaml
Titulo: [FULL-STACK] Implementar CRUD de Listas
Tipo: Epic
Sprint: 2
Pontos: 21

Descricao: |
  Sistema completo de listas de candidatos com criacao,
  edicao, exclusao e gerenciamento de membros.

Historia de Usuario: |
  Como recrutador, eu quero criar e gerenciar listas
  de candidatos para organizar meu trabalho.

Regras de Negocio:
  1. Nome obrigatorio e unico
  2. Cor selecionavel
  3. Limite de 100 listas
  4. Candidatos podem estar em multiplas listas
  5. Excluir lista nao exclui candidatos

Requisitos Tecnicos:
  Frontend:
    - ListsTab com grid de cards
    - CreateListModal com form
    - ColorPicker (8 cores)
    - ListDetailView
    - AddToListModal
  Backend:
    - CRUD /api/v1/candidate-lists
    - Nested /candidates
    - Validacao de unicidade
  Dados:
    - candidate_lists
    - candidate_list_items

DoD:
  - [ ] Criar lista funciona
  - [ ] Editar funciona
  - [ ] Excluir funciona
  - [ ] Adicionar candidatos funciona
  - [ ] Remover candidatos funciona
  - [ ] Duplicatas tratadas

Criterios de Aceitacao:
  - [ ] Criar "Projeto Alpha" funciona
  - [ ] Erro se nome duplicado
  - [ ] Adicionar 5 candidatos funciona
  - [ ] Excluir lista mantem candidatos
```

---

## 6. Diagrama da Jornada do Fluxo

### Criar Lista e Adicionar Candidatos

```
INICIO
  |
  v
[Usuario esta na tab Busca com resultados]
  |
  v
[Seleciona 5 candidatos (checkbox)]
  |
  v
[Banner de acoes aparece]
  |
  v
[Clica em "Adicionar a Lista"]
  |
  v
[FRONT] Abre AddToListModal
  |
  v
[Lista existente? Nao, criar nova]
  |
  v
[Clica em "Criar Nova Lista"]
  |
  v
[FRONT] Form inline aparece
  |
  v
[Digita "Projeto Alpha" e escolhe cor azul]
  |
  v
[Clica em "Criar e Adicionar"]
  |
  v
[BACK] POST /api/v1/candidate-lists
  |
  v
[DADOS] INSERT INTO candidate_lists
  |
  v
[BACK] POST /api/v1/candidate-lists/{id}/candidates
  |
  v
[DADOS] INSERT INTO candidate_list_items (5 rows)
  |
  v
[FRONT] Fecha modal
  |
  v
[FRONT] Toast: "5 candidatos adicionados a Projeto Alpha"
  |
  v
[Usuario vai para tab Listas]
  |
  v
[Card "Projeto Alpha" aparece com badge "5"]
  |
  v
[Clica no card]
  |
  v
[BACK] GET /api/v1/candidate-lists/{id}
  |
  v
[FRONT] ListDetailView com 5 candidatos
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: CRUD Basico (Sprint 2)
```
[Criar lista]
      |
      v
[Listar listas]
      |
      v
[Editar lista]
      |
      v
[Excluir lista]
```

### Fase 2: Gestao de Membros (Sprint 2)
```
[Adicionar candidatos]
        |
        v
[Remover candidatos]
        |
        v
[Ver detalhe da lista]
```

### Fase 3: Integracoes (Sprint 3)
```
[Vincular a vagas]
        |
        v
[Exportar CSV/Excel]
```

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
LIS-F01-T1,[BACK] API GET Listas,feature,3h
LIS-F02-T1,[BACK] API POST Criar,feature,3h
LIS-F02-T2,[FRONT] CreateListModal,feature,5h
LIS-F02-T3,[FRONT] ColorPicker,feature,2h
LIS-F03-T1,[BACK] API PUT Editar,feature,2h
LIS-F04-T1,[BACK] API DELETE Excluir,feature,2h
LIS-F04-T2,[FRONT] ConfirmDialog,feature,2h
LIS-F05-T1,[BACK] API GET Detalhe,feature,3h
LIS-F05-T2,[FRONT] ListDetailView,feature,5h
LIS-F06-T1,[BACK] API POST Adicionar,feature,3h
LIS-F06-T2,[FRONT] AddToListModal,feature,5h
LIS-F07-T1,[BACK] API DELETE Remover,feature,2h
LIS-F08-T1,[BACK] API Vincular Vagas,feature,4h
LIS-F08-T2,[FRONT] LinkToVacancyModal,feature,4h
LIS-F09-T1,[BACK] API Export,feature,4h
LIS-F09-T2,[FRONT] ExportModal,feature,3h
```

---

## 9. Padrao de Design

### Vuetify 3

```vue
<!-- Grid de Listas -->
<v-row>
  <v-col v-for="list in lists" :key="list.id" cols="12" sm="6" md="4">
    <v-card variant="outlined" class="pa-4" @click="openList(list)">
      <div class="d-flex align-center gap-3">
        <v-avatar :color="list.color" size="40">
          <v-icon icon="mdi-account-group" color="white" />
        </v-avatar>
        <div class="flex-grow-1">
          <div class="text-subtitle-1 font-weight-medium">
            {{ list.name }}
          </div>
          <div class="text-caption text-grey">
            {{ list.candidates_count }} candidatos
          </div>
        </div>
        <v-menu>
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-dots-vertical" variant="text" />
          </template>
          <v-list density="compact">
            <v-list-item @click="editList(list)">
              <v-list-item-title>Editar</v-list-item-title>
            </v-list-item>
            <v-list-item @click="deleteList(list)" class="text-error">
              <v-list-item-title>Excluir</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </v-card>
  </v-col>
</v-row>

<!-- CreateListModal -->
<v-dialog v-model="showModal" max-width="500">
  <v-card>
    <v-card-title>Nova Lista</v-card-title>
    <v-card-text>
      <v-text-field
        v-model="form.name"
        label="Nome da lista"
        variant="outlined"
        :rules="[v => !!v || 'Nome obrigatorio']"
      />
      <v-textarea
        v-model="form.description"
        label="Descricao (opcional)"
        variant="outlined"
        rows="2"
      />
      <div class="d-flex gap-2 mt-4">
        <v-btn
          v-for="color in colors"
          :key="color"
          :color="color"
          :variant="form.color === color ? 'flat' : 'tonal'"
          icon
          size="small"
          @click="form.color = color"
        />
      </div>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="showModal = false">Cancelar</v-btn>
      <v-btn color="primary" @click="createList">Criar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

---

## 10. Uso de IA no Fluxo

**Este fluxo NAO utiliza IA diretamente.**

Possivel expansao futura: LIA sugerir listas baseado em perfil do candidato.

---

# FLUXO 04: HISTORICO E REUTILIZACAO

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Historico de Buscas e Buscas Salvas**

### O que esse fluxo entrega
Sistema de historico automatico de buscas com opcao de salvar, re-executar e gerenciar.

### Para qual usuario
- Recrutador

### Resultado final esperado
Acesso rapido a buscas anteriores com possibilidade de reutilizacao.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| HistoryTab | Tab de historico |
| HistoryList | Lista agrupada por data |
| HistoryItem | Item do historico |
| SavedSearchesTab | Tab de buscas salvas |
| SavedSearchCard | Card de busca salva |
| SaveSearchModal | Modal para salvar |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/search-history | GET | Listar historico |
| /api/v1/search-history | POST | Salvar no historico |
| /api/v1/search-history/{id} | DELETE | Excluir item |
| /api/v1/saved-searches | GET | Listar salvas |
| /api/v1/saved-searches | POST | Salvar busca |
| /api/v1/saved-searches/{id} | PUT | Editar |
| /api/v1/saved-searches/{id} | DELETE | Excluir |

### Dados

| Tabela | Campos |
|--------|--------|
| search_history | id, user_id, query, mode, source, entities, filters, results_count, created_at |
| saved_searches | id, user_id, name, description, query, mode, source, entities, filters, is_favorite, usage_count, last_used_at |

---

## 3. Lista Completa de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| HIS-F01 | Salvar Automatico | Toda busca vai pro historico |
| HIS-F02 | Listar Historico | Agrupado por data |
| HIS-F03 | Re-executar | Rodar busca do historico |
| HIS-F04 | Salvar como Favorita | Promover para busca salva |
| HIS-F05 | Excluir Item | Remover do historico |
| HIS-F06 | Limpar Tudo | Apagar historico |
| SAV-F01 | Criar Busca Salva | Salvar com nome |
| SAV-F02 | Listar Salvas | Ver todas |
| SAV-F03 | Executar Salva | Rodar busca |
| SAV-F04 | Favoritar | Marcar como prioritaria |
| SAV-F05 | Editar | Alterar nome/descricao |
| SAV-F06 | Excluir | Remover busca salva |
| SAV-F07 | Ver Stats | Vezes usada, media resultados |

---

## 4. Documentacao Detalhada

### HIS-F01: Salvar Automatico

#### Historia de Usuario
"Como sistema, eu preciso salvar cada busca no historico para analise e reutilizacao."

#### Regras de Negocio
1. Salvar apos cada busca executada
2. Armazenar: query, modo, fonte, entidades, filtros, resultados
3. Limite de 100 ultimas buscas
4. Mais antigas sao excluidas automaticamente
5. Buscas identicas em <5min nao duplicam

#### Formulas e Logicas
```
fingerprint = hash(query + mode + source + sort(filters))

Se busca com mesmo fingerprint nos ultimos 5 minutos:
  Atualizar results_count da existente
  Nao criar novo registro
Senao:
  Criar novo registro
  Se total > 100:
    DELETE mais antigas
```

---

### SAV-F03: Executar Busca Salva

#### Historia de Usuario
"Como recrutador, eu quero executar uma busca salva com um clique."

#### Regras de Negocio
1. Clicar em "Executar" ou no card
2. Redirecionar para tab Busca
3. Aplicar todos os parametros salvos
4. Incrementar usage_count
5. Atualizar last_used_at

#### Inputs
- saved_search_id (string)

#### Outputs
- Redirect para tab Busca
- Parametros aplicados
- Busca executada

---

## 5. Cards de Especificacao

### CARD HIS-FLOW-001: Sistema de Historico

```yaml
Titulo: [FULL-STACK] Implementar Sistema de Historico
Tipo: Feature
Sprint: 2
Pontos: 13

Descricao: |
  Sistema de historico automatico com agrupamento por data
  e acoes de re-execucao e salvamento.

DoD:
  - [ ] Busca salva automaticamente no historico
  - [ ] Historico lista agrupado por data
  - [ ] Re-executar funciona
  - [ ] Salvar como favorita funciona
  - [ ] Excluir item funciona
  - [ ] Limpar tudo funciona
```

### CARD SAV-FLOW-001: Sistema de Buscas Salvas

```yaml
Titulo: [FULL-STACK] Implementar Buscas Salvas
Tipo: Feature
Sprint: 2
Pontos: 13

Descricao: |
  Sistema de buscas salvas com favoritos, estatisticas
  e execucao rapida.

DoD:
  - [ ] Criar busca salva funciona
  - [ ] Listar funciona
  - [ ] Executar funciona
  - [ ] Favoritar funciona
  - [ ] Stats exibidas
  - [ ] Excluir funciona
```

---

## 6. Diagrama da Jornada do Fluxo

```
INICIO
  |
  v
[Usuario executa busca na tab Busca]
  |
  v
[BACK] Automaticamente salva no historico
  |
  v
[Dias depois, usuario acessa tab Historico]
  |
  v
[FRONT] Lista agrupada: Hoje, Ontem, Ultimos 7 dias
  |
  v
[Usuario encontra busca de 3 dias atras]
  |
  v
[Clica em "Executar"]
  |
  v
[FRONT] Navega para tab Busca com parametros]
  |
  v
[Busca executada com mesmos parametros]
  |
  v
[Usuario decide salvar essa busca]
  |
  v
[Clica em "Salvar Busca" na area de resultados]
  |
  v
[FRONT] SaveSearchModal abre
  |
  v
[Usuario digita nome: "Dev React SP"]
  |
  v
[BACK] POST /api/v1/saved-searches
  |
  v
[FRONT] Toast: "Busca salva com sucesso"]
  |
  v
[Usuario vai para tab Buscas Salvas]
  |
  v
[Card "Dev React SP" aparece]
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: Historico Basico (Sprint 2)
```
[Auto-save]
     |
     v
[Listar agrupado]
     |
     v
[Re-executar]
```

### Fase 2: Buscas Salvas (Sprint 2)
```
[Criar busca salva]
        |
        v
[Listar e executar]
        |
        v
[Favoritar]
```

### Fase 3: Enriquecimento (Sprint 3)
```
[Estatisticas de uso]
         |
         v
[Ordenacao inteligente]
```

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
HIS-F01-T1,[BACK] Auto-save Historico,feature,3h
HIS-F02-T1,[FRONT] HistoryTab,feature,5h
HIS-F02-T2,[FRONT] Agrupamento por Data,feature,3h
HIS-F03-T1,[FRONT] Re-executar Busca,feature,3h
HIS-F04-T1,[FRONT] Promover para Salva,feature,3h
HIS-F05-T1,[FRONT] Excluir Item,feature,2h
HIS-F06-T1,[FRONT] Limpar Historico,feature,2h
SAV-F01-T1,[BACK] API POST Saved,feature,3h
SAV-F01-T2,[FRONT] SaveSearchModal,feature,4h
SAV-F02-T1,[BACK] API GET Saved,feature,2h
SAV-F02-T2,[FRONT] SavedSearchesTab,feature,5h
SAV-F03-T1,[FRONT] Executar Salva,feature,3h
SAV-F04-T1,[FRONT] Toggle Favoritar,feature,2h
SAV-F07-T1,[FRONT] Stats Display,feature,2h
```

---

## 9. Padrao de Design

```vue
<!-- Historico agrupado -->
<template v-for="group in groupedHistory" :key="group.label">
  <div class="text-overline text-grey mb-2">{{ group.label }}</div>
  <v-list density="compact">
    <v-list-item
      v-for="item in group.items"
      :key="item.id"
    >
      <template #prepend>
        <v-icon :icon="getModeIcon(item.mode)" />
      </template>
      <v-list-item-title>{{ item.query }}</v-list-item-title>
      <v-list-item-subtitle>
        {{ item.results_count }} resultados
      </v-list-item-subtitle>
      <template #append>
        <v-btn icon="mdi-play" size="small" @click="reExecute(item)" />
        <v-btn icon="mdi-bookmark" size="small" @click="saveSearch(item)" />
      </template>
    </v-list-item>
  </v-list>
</template>
```

---

## 10. Uso de IA no Fluxo

**Este fluxo NAO utiliza IA diretamente.**

As entidades salvas no historico foram extraidas pela IA no momento da busca original.

---

# FLUXO 05: BUSCA GLOBAL PEARCH

> **Status:** ✅ IMPLEMENTADO (Dezembro 2024)

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Busca Híbrida com Pearch AI**

### O que esse fluxo entrega
Acesso a mais de 800 milhões de perfis profissionais via integração Pearch com sistema de créditos e busca híbrida (local + global).

### Para qual usuario
- Recrutador
- Headhunter
- Tech Recruiter

### Resultado final esperado
Candidatos globais descobertos, importados para staging table, e promovidos para base local após revelação de contatos.

### Configuração Obrigatória
```bash
# Adicionar via Replit Secrets
PEARCH_API_KEY=<sua-api-key-pearch>
```

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Arquivo | Descricao |
|------------|---------|-----------|
| SourceSelector | smart-search-input.tsx | Toggle Local/Global/Híbrido |
| CreditConfirmDialog | credit-confirmation-dialog.tsx | Confirmação de gasto |
| CreditCostDisplay | credit-cost-display.tsx | Exibição de custos |
| AdvancedFiltersModal | advanced-filters-modal.tsx | Filtros avançados com SearchSpec |
| UnifiedCandidateTable | unified-candidate-table.tsx | Tabela com badge "Pearch" |
| CandidatePreview | candidate-preview.tsx | Preview com dados Pearch |

### Backend

| Endpoint | Metodo | Descricao | Status |
|----------|--------|-----------|--------|
| /api/v1/search/candidates | POST | Busca híbrida (local + Pearch) | ✅ |
| /api/v1/search/candidates/import | POST | Importar para staging table | ✅ |
| /api/v1/candidates/promote/{id} | POST | Promover para base principal | ✅ |
| /api/v1/search/parse-query | POST | Parsing de query para filtros | ✅ |
| /api/v1/enhance-prompt | POST | Enhancement de query com IA | ✅ |

### Dados

| Tabela | Campos | Descricao |
|--------|--------|-----------|
| external_candidate_profiles | id, pearch_id, name, email, phone, skills, etc | Staging table - candidatos descobertos |
| candidates | source, pearch_profile_id | Base principal - candidatos promovidos |
| candidate_experiences | company_info, funding_stage, industries | Experiências com dados ricos de empresa |
| candidate_education | institution_tier, institution_country | Formação com dados de instituição |

### Integracoes Externas

| Servico | Uso | Status |
|---------|-----|--------|
| Pearch API v2 | Busca global de candidatos | ✅ Implementado |
| Anthropic Claude | SearchSpec parsing e análise | ✅ Implementado |

---

## 3. Lista Completa de Funcionalidades

| ID | Funcionalidade | Descricao | Status |
|----|----------------|-----------|--------|
| PEA-F01 | Selecionar Fonte Híbrida | Toggle Local/Global/Híbrido | ✅ |
| PEA-F02 | Estimar Créditos | Mostrar custo antes de buscar | ✅ |
| PEA-F03 | Confirmar Gasto | Dialog de confirmação | ✅ |
| PEA-F04 | Executar Busca Híbrida | Buscar local + Pearch | ✅ |
| PEA-F05 | Exibir Resultados Combinados | Candidatos locais + Pearch | ✅ |
| PEA-F06 | Importar para Staging | Salvar em external_candidate_profiles | ✅ |
| PEA-F07 | Promover para Base | Mover staging → candidates | ✅ |
| PEA-F08 | Ver Saldo de Créditos | Exibir créditos restantes | ✅ |
| PEA-F09 | SearchSpec Avançado | Filtros estruturados | ✅ |
| PEA-F10 | Filtros de Empresa | funding_stage, company_tags, etc | ✅ |
| PEA-F11 | Filtros de Formação | institution_tier, ranking, etc | ✅ |

### Sistema de Créditos Pearch

```
Custos por candidato:
- fast: 1 crédito base
- pro: 5 créditos base
- insights: +1 crédito
- profile_scoring: +1 crédito
- high_freshness: +2 créditos
- require_emails: +1 crédito
- show_emails: +2 créditos (só cobra se tiver email)
- require_phone_numbers: +1 crédito
- show_phone_numbers: +14 créditos (só cobra se tiver telefone)
```

### SearchSpec - Filtros Estruturados

O SearchSpec é extraído automaticamente da query ou configurado via modal de filtros:

```json
{
  "location": "São Paulo, SP",
  "skills": ["Ruby", "Rails", "PostgreSQL"],
  "seniority": "senior",
  "experience_years_min": 5,
  "industries": ["technology", "fintech"],
  "funding_stages": ["series_a", "series_b"],
  "company_hq_countries": ["Brazil", "USA"],
  "institution_tiers": ["tier1", "tier2"],
  "languages": ["Portuguese", "English"]
}
```

---

## 4. Documentacao Detalhada

### PEA-F06: Revelar Contatos

#### Historia de Usuario
"Como recrutador, eu quero revelar o contato de um candidato global para poder aborda-lo."

#### Regras de Negocio
1. Candidatos Pearch nao tem contato visivel inicialmente
2. Botao "Revelar" mostra custo (1 credito)
3. Confirmacao obrigatoria antes de debitar
4. Contatos revelados: email, telefone, LinkedIn
5. Candidato e automaticamente salvo na base local
6. Revelacao e persistente (nao cobra novamente)

#### Formulas e Logicas
```
custo_revelacao = 1 credito

Se ja revelado anteriormente:
  Retornar dados do cache
  Nao debitar credito

Se nao revelado:
  Se saldo >= 1:
    Chamar Pearch reveal API
    Debitar 1 credito
    Salvar candidato na base local
    Retornar contatos
  Senao:
    Erro: "Creditos insuficientes"
    Oferecer compra
```

#### Inputs
- pearch_profile_id (string)

#### Outputs
```json
{
  "email": "joao@email.com",
  "phone": "+55 11 99999-9999",
  "linkedin": "linkedin.com/in/joaosilva",
  "candidate_id": "uuid-local",
  "credits_remaining": 49
}
```

#### Validacoes
- Saldo de creditos suficiente
- pearch_id valido

#### Edge Cases
- Pearch API falha: retry com backoff, nao debitar
- Candidato sem email: retornar apenas telefone
- Candidato ja na base: vincular ao existente

---

## 5. Cards de Especificacao

### CARD PEA-FLOW-001: Integracao Pearch Completa

```yaml
Titulo: [FULL-STACK] Implementar Integracao Pearch
Tipo: Epic
Sprint: 4
Pontos: 34

Descricao: |
  Integracao completa com Pearch para busca global
  de candidatos com sistema de creditos.

Historia de Usuario: |
  Como recrutador, eu quero buscar em uma base global
  de 800M+ perfis para encontrar talentos raros.

Regras de Negocio:
  1. Busca global consome creditos
  2. Estimativa antes de buscar
  3. Confirmacao antes de gastar
  4. Revelacao custa 1 credito
  5. Candidatos revelados salvos localmente
  6. Saldo visivel no header

Requisitos Tecnicos:
  Frontend:
    - SourceSelector com Global
    - CreditEstimateToast
    - CreditConfirmDialog
    - RevealContactButton
    - CreditBalanceBadge
  Backend:
    - Integracao Pearch API
    - Sistema de creditos
    - Cache de revelacoes
    - Mapeamento Pearch -> Local
  Dados:
    - pearch_credits
    - pearch_reveals
    - candidates.source = 'pearch'

Integracoes:
  - Pearch API (search, reveal)
  - Sistema de pagamentos (compra creditos)

Riscos:
  - Pearch indisponivel: fallback para local only
  - Creditos insuficientes: bloquear e oferecer compra
  - Dados desatualizados: cache com TTL

DoD:
  - [ ] Toggle Global funciona
  - [ ] Estimativa exibida
  - [ ] Confirmacao funciona
  - [ ] Busca retorna resultados
  - [ ] Revelacao funciona
  - [ ] Creditos debitados
  - [ ] Candidato salvo local
  - [ ] Saldo atualizado

Criterios de Aceitacao:
  - [ ] Buscar "Python SP" retorna perfis Pearch
  - [ ] Revelar mostra email e telefone
  - [ ] Credito e debitado
  - [ ] Candidato aparece em busca local
```

---

## 6. Diagrama da Jornada do Fluxo

```
INICIO
  |
  v
[Usuario seleciona fonte "Global (Pearch)"]
  |
  v
[FRONT] Exibe badge de creditos no header
  |
  v
[Usuario digita query: "Data Scientist ML"]
  |
  v
[Usuario clica em Buscar]
  |
  v
[FRONT] Exibe CreditEstimateToast
  |
  +-- "Esta busca pode retornar ate 500 perfis"
  |
  v
[FRONT] Abre CreditConfirmDialog
  |
  +-- "Deseja prosseguir? Custo: estimativa de creditos para revelar"
  |
  v
[Usuario confirma]
  |
  v
[BACK] POST /api/v1/pearch/search
  |
  v
[INTEGRACOES] Pearch API retorna perfis
  |
  v
[FRONT] Renderiza tabela com badge "Global"
  |
  +-- Contatos ocultos (blur)
  |
  v
[Usuario clica em "Revelar Contato" no candidato X]
  |
  v
[FRONT] CreditConfirmDialog
  |
  +-- "Revelar contato por 1 credito?"
  |
  v
[Usuario confirma]
  |
  v
[BACK] POST /api/v1/pearch/reveal/{pearch_id}
  |
  v
[INTEGRACOES] Pearch reveal API
  |
  v
[BACK] Debita 1 credito
  |
  v
[DADOS] INSERT INTO candidates (source='pearch')
  |
  v
[DADOS] INSERT INTO pearch_reveals
  |
  v
[BACK] Retorna contatos + candidate_id local
  |
  v
[FRONT] Exibe email e telefone
  |
  v
[FRONT] Atualiza badge de creditos
  |
  v
[FRONT] Toast: "Contato revelado e candidato salvo"
  |
FIM
```

---

## 7. Roadmap do Fluxo

### Fase 1: Busca Global (Sprint 4)
```
[Toggle fonte Global]
         |
         v
[Integracao Pearch Search]
         |
         v
[Exibir resultados com badge]
```

### Fase 2: Revelacao (Sprint 4)
```
[Botao Revelar]
       |
       v
[Confirmacao de credito]
       |
       v
[Revelar e salvar local]
```

### Fase 3: Gestao de Creditos (Sprint 5)
```
[Saldo no header]
        |
        v
[Historico de gastos]
        |
        v
[Compra de creditos]
```

---

## 8. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
PEA-F01-T1,[FRONT] SourceSelector Global,feature,2h
PEA-F02-T1,[BACK] API Estimate,feature,3h
PEA-F02-T2,[FRONT] CreditEstimateToast,feature,2h
PEA-F03-T1,[FRONT] CreditConfirmDialog,feature,3h
PEA-F04-T1,[BACK] Integracao Pearch Search,feature,8h
PEA-F04-T2,[BACK] Mapeamento Response,feature,3h
PEA-F05-T1,[FRONT] GlobalCandidateCard,feature,3h
PEA-F06-T1,[BACK] API Reveal,feature,5h
PEA-F06-T2,[FRONT] RevealContactButton,feature,3h
PEA-F06-T3,[FRONT] RevealedContactCard,feature,3h
PEA-F07-T1,[BACK] Salvar na Base Local,feature,4h
PEA-F08-T1,[FRONT] CreditBalanceBadge,feature,2h
PEA-F08-T2,[BACK] API Get Balance,feature,2h
```

---

## 9. Padrao de Design

```vue
<!-- Badge de Creditos -->
<v-chip color="primary" variant="tonal" size="small">
  <v-icon start icon="mdi-coin" />
  {{ credits }} creditos
</v-chip>

<!-- CreditConfirmDialog -->
<v-dialog v-model="showConfirm" max-width="400">
  <v-card>
    <v-card-title>Confirmar revelacao</v-card-title>
    <v-card-text>
      <div class="d-flex align-center gap-3 mb-4">
        <v-avatar size="48">
          <v-img :src="candidate.avatar" />
        </v-avatar>
        <div>
          <div class="text-subtitle-1">{{ candidate.name }}</div>
          <div class="text-caption text-grey">{{ candidate.title }}</div>
        </div>
      </div>
      <v-alert type="info" variant="tonal">
        Esta acao custara <strong>1 credito</strong>.
        Saldo atual: {{ credits }} creditos.
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="showConfirm = false">Cancelar</v-btn>
      <v-btn color="primary" @click="reveal">Revelar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>

<!-- Candidato Global (antes de revelar) -->
<v-card variant="outlined">
  <v-card-text>
    <div class="d-flex align-center gap-3">
      <v-avatar size="48">
        <v-img :src="candidate.avatar" />
      </v-avatar>
      <div class="flex-grow-1">
        <div class="d-flex align-center gap-2">
          <span class="text-subtitle-1">{{ candidate.name }}</span>
          <v-chip size="x-small" color="blue-grey" variant="tonal">
            Global
          </v-chip>
        </div>
        <div class="text-caption text-grey">{{ candidate.title }}</div>
      </div>
      <v-btn color="primary" variant="tonal" @click="revealContact">
        <v-icon start icon="mdi-eye" />
        Revelar (1 credito)
      </v-btn>
    </div>
  </v-card-text>
</v-card>
```

---

## 10. Uso de IA no Fluxo

**Este fluxo NAO utiliza IA diretamente no frontend.**

A busca do Pearch usa seus proprios algoritmos de matching.

Possivel expansao: LIA analisar perfil Pearch e dar parecer antes de revelar.

---

# FLUXO 06: VINCULACAO A VAGAS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Vincular Candidatos a Vagas**

### O que esse fluxo entrega
Conexao entre candidatos encontrados no Funil e vagas abertas no Kanban.

### Para qual usuario
- Recrutador

### Resultado final esperado
Candidatos adicionados ao pipeline de uma vaga especifica.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| AddToVacancyButton | Botao de vincular |
| AddToVacancyModal | Modal de selecao de vaga |
| VacancySearchInput | Busca de vagas |
| VacancyCard | Card de vaga no modal |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/jobs | GET | Listar vagas abertas |
| /api/v1/jobs/{id}/candidates | POST | Adicionar candidatos |

### Dados

| Tabela | Campos |
|--------|--------|
| jobs | id, title, status, company_id |
| job_candidates | job_id, candidate_id, stage, added_at |

---

## 3. Lista Completa de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| VIN-F01 | Listar Vagas Abertas | Vagas disponiveis para vinculo |
| VIN-F02 | Buscar Vaga | Filtrar por nome |
| VIN-F03 | Selecionar Vaga | Escolher destino |
| VIN-F04 | Vincular Candidato | Adicionar a vaga |
| VIN-F05 | Vincular Multiplos | Adicionar em lote |
| VIN-F06 | Detectar Duplicata | Avisar se ja na vaga |
| VIN-F07 | Vincular Lista Inteira | Adicionar lista completa |

---

## 4. Documentacao Detalhada

### VIN-F04: Vincular Candidato

#### Historia de Usuario
"Como recrutador, eu quero adicionar um candidato a uma vaga para iniciar o processo seletivo."

#### Regras de Negocio
1. Candidato e adicionado no estagio inicial (Funil)
2. Se ja existe na vaga, avisar e nao duplicar
3. Registrar data de adicao
4. Notificar gestor da vaga (opcional)

#### Inputs
```json
{
  "candidate_ids": ["uuid1"],
  "job_id": "job-uuid"
}
```

#### Outputs
```json
{
  "added": 1,
  "already_in_job": 0,
  "job": {...}
}
```

---

## 5. Cards de Especificacao

### CARD VIN-FLOW-001: Vinculacao de Candidatos

```yaml
Titulo: [FULL-STACK] Implementar Vinculacao a Vagas
Tipo: Feature
Sprint: 3
Pontos: 13

DoD:
  - [ ] Modal lista vagas abertas
  - [ ] Busca de vagas funciona
  - [ ] Vincular 1 candidato funciona
  - [ ] Vincular multiplos funciona
  - [ ] Duplicata detectada
  - [ ] Candidato aparece no Kanban
```

---

## 6. Diagrama da Jornada do Fluxo

```
INICIO
  |
  v
[Usuario seleciona candidatos na busca]
  |
  v
[Clica em "Adicionar a Vaga" no banner]
  |
  v
[BACK] GET /api/v1/jobs?status=open
  |
  v
[FRONT] AddToVacancyModal abre
  |
  v
[Usuario busca: "Desenvolvedor"]
  |
  v
[Lista filtrada de vagas]
  |
  v
[Usuario seleciona "Dev Python - Projeto X"]
  |
  v
[Clica em "Adicionar"]
  |
  v
[BACK] POST /api/v1/jobs/{id}/candidates
  |
  v
[DADOS] INSERT INTO job_candidates (stage='funil')
  |
  v
[FRONT] Toast: "3 candidatos adicionados a Dev Python"]
  |
  v
[Candidatos aparecem no Kanban da vaga]
  |
FIM
```

---

## 7. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
VIN-F01-T1,[BACK] API GET Jobs Open,feature,2h
VIN-F02-T1,[FRONT] VacancySearchInput,feature,2h
VIN-F03-T1,[FRONT] AddToVacancyModal,feature,5h
VIN-F04-T1,[BACK] API POST Vincular,feature,3h
VIN-F05-T1,[BACK] Batch Vincular,feature,3h
VIN-F06-T1,[BACK] Detectar Duplicata,feature,2h
```

---

# FLUXO 07: COMUNICACAO COM CANDIDATOS

---

## 1. Nome e Objetivo do Fluxo

### Nome
**Comunicacao com Candidatos**

### O que esse fluxo entrega
Envio de emails e WhatsApp para candidatos diretamente da plataforma.

### Para qual usuario
- Recrutador

### Resultado final esperado
Mensagem enviada e registrada no historico do candidato.

---

## 2. Paginas, Modulos e Areas Envolvidas

### Frontend

| Componente | Descricao |
|------------|-----------|
| EmailButton | Botao de email |
| WhatsAppButton | Botao de WhatsApp |
| UnifiedCommunicationModal | Modal de comunicacao |
| TemplateSelector | Seletor de templates |
| MessageEditor | Editor de mensagem |

### Backend

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| /api/v1/templates | GET | Listar templates |
| /api/v1/communications | POST | Enviar mensagem |
| /api/v1/candidates/{id}/communications | GET | Historico |

---

## 3. Lista Completa de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| COM-F01 | Selecionar Canal | Email ou WhatsApp |
| COM-F02 | Escolher Template | Templates pre-definidos |
| COM-F03 | Personalizar Mensagem | Editar texto |
| COM-F04 | Inserir Variaveis | {nome}, {cargo}, etc |
| COM-F05 | Enviar Email | Via API de email |
| COM-F06 | Enviar WhatsApp | Via wa.me ou API |
| COM-F07 | Registrar Historico | Log de envios |
| COM-F08 | Ver Historico | Timeline de comunicacoes |

---

## 4. Documentacao Detalhada

### COM-F05: Enviar Email

#### Historia de Usuario
"Como recrutador, eu quero enviar email para um candidato diretamente da plataforma."

#### Regras de Negocio
1. Email do remetente e o do recrutador
2. Templates com variaveis {nome}, {vaga}, {empresa}
3. Assunto obrigatorio
4. Corpo com rich text basico
5. Anexos opcionais (CV, JD)
6. Registrar no historico do candidato

#### Inputs
```json
{
  "candidate_id": "uuid",
  "channel": "email",
  "template_id": "uuid" (opcional),
  "subject": "Oportunidade em...",
  "body": "Ola {nome}...",
  "attachments": []
}
```

#### Outputs
```json
{
  "communication_id": "uuid",
  "status": "sent",
  "sent_at": "2024-12-01T10:00:00Z"
}
```

---

## 5. Cards de Especificacao

### CARD COM-FLOW-001: Sistema de Comunicacao

```yaml
Titulo: [FULL-STACK] Implementar Comunicacao
Tipo: Epic
Sprint: 3
Pontos: 21

DoD:
  - [ ] Modal de comunicacao funciona
  - [ ] Templates carregam
  - [ ] Variaveis substituidas
  - [ ] Email envia
  - [ ] WhatsApp abre/envia
  - [ ] Historico registrado
```

---

## 6. Diagrama da Jornada

```
INICIO
  |
  v
[Usuario clica em "Email" no preview do candidato]
  |
  v
[FRONT] UnifiedCommunicationModal abre
  |
  v
[BACK] GET /api/v1/templates?channel=email
  |
  v
[Usuario seleciona template "Convite para Entrevista"]
  |
  v
[FRONT] Mensagem pre-preenchida com variaveis]
  |
  v
[Usuario edita e personaliza]
  |
  v
[Clica em "Enviar"]
  |
  v
[BACK] POST /api/v1/communications
  |
  v
[INTEGRACOES] Enviar via SendGrid/SES
  |
  v
[DADOS] INSERT INTO candidate_communications
  |
  v
[FRONT] Toast: "Email enviado com sucesso"]
  |
  v
[FRONT] Modal fecha
  |
FIM
```

---

## 7. Tasks Importaveis

```csv
ID,Titulo,Tipo,Est
COM-F01-T1,[FRONT] UnifiedCommunicationModal,feature,6h
COM-F02-T1,[BACK] API GET Templates,feature,3h
COM-F02-T2,[FRONT] TemplateSelector,feature,3h
COM-F03-T1,[FRONT] MessageEditor,feature,4h
COM-F04-T1,[BACK] Variable Substitution,feature,3h
COM-F05-T1,[BACK] Integracao Email,feature,5h
COM-F06-T1,[BACK] Integracao WhatsApp,feature,5h
COM-F07-T1,[BACK] Salvar Historico,feature,2h
COM-F08-T1,[FRONT] Timeline Comunicacoes,feature,4h
```

---

# RESUMO EXECUTIVO

## Status de Implementação (Dezembro 2024)

| Fluxo | Funcionalidades | Status | Progresso |
|-------|-----------------|--------|-----------|
| 01 - Busca | 20 | ✅ Implementado | 100% |
| 02 - Favoritos | 10 | ✅ Implementado | 100% |
| 03 - Listas | 10 | ✅ Implementado | 100% |
| 04 - Histórico | 13 | ✅ Implementado | 100% |
| 05 - Pearch Global | 11 | ✅ Implementado | 100% |
| 06 - Vagas | 7 | ✅ Implementado | 100% |
| 07 - Comunicação | 8 | ✅ Implementado | 100% |
| **TOTAL** | **79** | **Completo** | **100%** |

## Arquitetura Implementada

### Frontend (React/Next.js)
```
plataforma-lia/src/
├── components/
│   ├── search/                    # Componentes de busca
│   │   ├── smart-search-input.tsx
│   │   ├── advanced-filters-modal.tsx
│   │   ├── credit-confirmation-dialog.tsx
│   │   └── ...filtros especializados
│   ├── talent-funnel-tabs/        # Tabs do funil
│   │   ├── favorites-tab.tsx
│   │   ├── lists-tab.tsx
│   │   ├── history-tab.tsx
│   │   ├── saved-searches-tab.tsx
│   │   ├── pipelines-tab.tsx
│   │   ├── personas-tab.tsx
│   │   └── mapping-tab.tsx
│   └── pages/
│       └── candidates-page.tsx    # Página principal
├── hooks/
│   └── use-talent-funnel.ts       # Hook central
└── services/
    └── candidate-service.ts       # Serviço de candidatos
```

### Backend (FastAPI/Python)
```
lia-agent-system/app/
├── api/v1/
│   └── candidate_search.py        # Endpoints de busca
├── services/
│   └── pearch_service.py          # Integração Pearch
└── models/
    ├── pearch.py                  # Modelos Pearch
    └── candidate.py               # Modelos de candidato
```

## Configuração Necessária

```bash
# Secrets obrigatórios (Replit Secrets)
PEARCH_API_KEY=<api-key-pearch>
```

## Experience Highlights (Dezembro 2024)

Feature de resumos de experiência gerados por IA para leitura rápida pelo recrutador:

### Funcionalidade
- **Highlight Text**: Resumo de 1-2 frases sobre a experiência profissional do candidato
- **Geração por IA**: Utiliza Claude 3.5 Sonnet para analisar experiências e skills
- **Cache de 35 dias**: Evita chamadas repetidas à LLM, economizando créditos
- **Fallback**: Gera resumo simples sem IA caso ANTHROPIC_API_KEY não esteja configurada

### Endpoints
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| /api/v1/experience-highlights/{candidate_id} | GET | Buscar highlight em cache |
| /api/v1/experience-highlights/generate | POST | Gerar ou buscar highlight |
| /api/v1/experience-highlights/{candidate_id} | DELETE | Remover cache |
| /api/v1/experience-highlights/batch-generate | POST | Gerar para múltiplos candidatos |

### Componente Frontend
- `ExperienceHighlightCard`: Card branco com ícone ✨ e texto em negrito
- Posição: Abaixo das tabs e acima do parecer LIA na visualização do candidato
- Estados: Loading, Error, Cached, Regenerating

### Exemplo de Highlight
> ✨ **Rafael Iga is a Software Engineer with expertise in Ruby on Rails and has been working in Sao Paulo since January 2020. He has extensive experience in web development with Ruby on Rails and has also developed mobile applications.**

---

## Próximos Passos (Roadmap Futuro)

1. **Mapeamento de Mercado** - Análise de concorrentes e tendências
2. **Arquetipos com IA** - Geração automática de personas
3. **Analytics Avançado** - Dashboard de métricas de busca
4. **Integração ATS** - Conexão com sistemas externos

---

*Documento atualizado em Dezembro 2024.*
*Versão 2.0 - Funil de Talentos com integração Pearch completa.*
*Total: 7 fluxos implementados com 79 funcionalidades.*
