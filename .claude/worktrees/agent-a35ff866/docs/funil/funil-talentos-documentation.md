# DOCUMENTACAO COMPLETA - FUNIL DE TALENTOS

> **Versao:** 2.0  
> **Data:** Dezembro 2024  
> **Plataforma:** LIA - Learning Intelligence Assistant  
> **Stack Prototipo:** React/Next.js + Tailwind CSS + FastAPI  
> **Stack Producao:** Ruby on Rails + Vue.js/Nuxt + Vuetify

---

## INDICE

1. [Visao Geral do Modulo](#1-visao-geral-do-modulo)
2. [Paginas e Subpaginas](#2-paginas-e-subpaginas)
3. [Documentacao por Pagina/Tab](#3-documentacao-por-paginatab)
4. [Cards de Especificacao (Jira)](#4-cards-de-especificacao-jira)
5. [Diagramas de Jornada](#5-diagramas-de-jornada)
6. [Roadmap por Fases](#6-roadmap-por-fases)
7. [Padroes de Design](#7-padroes-de-design)
8. [Uso de IA](#8-uso-de-ia)
9. [Requisitos Funcionais](#9-requisitos-funcionais)
10. [Lista de Tasks Importavel](#10-lista-de-tasks-importavel)

---

## 1. VISAO GERAL DO MODULO

### 1.1 Nome do Modulo
**Funil de Talentos** (Talent Funnel / Candidates Page)

### 1.2 Objetivo Principal
Centralizar todas as operacoes de busca, descoberta, gestao e organizacao de candidatos na plataforma. E o hub principal de sourcing onde recrutadores encontram, avaliam, salvam e organizam talentos usando busca AI-powered, listas personalizadas, favoritos e historico de buscas.

### 1.3 Posicao na Jornada do Usuario
```
Login -> Dashboard -> FUNIL DE TALENTOS (Menu Principal)
                           |
                           +-> Busca de Candidatos
                           +-> Favoritos
                           +-> Listas
                           +-> Historico
                           +-> Buscas Salvas
                           +-> [Futuro] Mapeamento
                           +-> [Futuro] Personas
                           +-> [Futuro] Pipelines
```

### 1.4 Dependencias do Modulo

**Modulos que este depende:**
- Sistema de Autenticacao
- Base de Candidatos Local
- Integracao Pearch AI (busca global)
- Agentes LIA (triagem, analise)
- Sistema de Vagas (para vincular candidatos)
- Templates de Comunicacao

**Modulos que dependem deste:**
- Gestao de Vagas (Kanban) - recebe candidatos daqui
- Relatorios de Sourcing
- Analytics de Recrutamento
- Sistema de Calibracao

### 1.5 Status de Definicao

**Claramente Definido:**
- Tabs principais: Busca, Favoritos, Listas, Historico, Buscas Salvas
- Modos de busca: Natural, Similar, JD, Boolean, Arquetipos
- Fontes de busca: Local, Global (Pearch), Hibrido
- Sistema de favoritos com notas e pins
- Listas de candidatos com CRUD completo
- Historico de buscas com re-execucao
- Buscas salvas com estatisticas de uso
- Preview de candidato em painel lateral
- Acoes em lote (bulk actions)
- Upload de CV com parsing AI

**Em Aberto / Mal Definido:**
- Tab Mapeamento (mapping-tab.tsx existe mas funcionalidade incompleta)
- Tab Personas (personas-tab.tsx existe mas funcionalidade incompleta)
- Tab Pipelines (pipelines-tab.tsx existe mas funcionalidade incompleta)
- Limites de creditos para busca global
- Regras de revelacao de contatos Pearch
- Persistencia de filtros entre sessoes

---

## 2. PAGINAS E SUBPAGINAS

### 2.1 Estrutura de Navegacao

```
FUNIL DE TALENTOS (candidates-page.tsx)
|
+-- TAB: BUSCA (search) [Principal]
|   +-- SmartSearchInput (AI-powered)
|   |   +-- Modo Natural (Sparkles)
|   |   +-- Modo Perfil Similar (Users)
|   |   +-- Modo Job Description (FileText)
|   |   +-- Modo Boolean (Binary)
|   |   +-- Modo Arquetipos (Target)
|   +-- Seletor de Fonte (Local/Global/Hibrido)
|   +-- Filtros Avancados (AdvancedFiltersModal)
|   +-- Tabela de Resultados (UnifiedCandidateTable)
|   +-- Preview Lateral (CandidatePreview)
|   +-- Upload de CV (drag-drop)
|   +-- Prompt Expandido LIA
|
+-- TAB: FAVORITOS (favorites)
|   +-- Filtros: Todos/Fixados/Favoritos
|   +-- Busca por nome/cargo
|   +-- Notas por candidato
|   +-- Tabela de candidatos
|
+-- TAB: LISTAS (lists)
|   +-- Lista de listas criadas
|   +-- Criar nova lista
|   +-- Editar lista
|   +-- Excluir lista
|   +-- Adicionar candidatos a lista
|   +-- Vincular lista a vagas
|
+-- TAB: HISTORICO (history)
|   +-- Buscas recentes agrupadas por data
|   +-- Re-executar busca
|   +-- Salvar como busca favorita
|   +-- Limpar historico
|
+-- TAB: BUSCAS SALVAS (saved-searches)
|   +-- Lista de buscas salvas
|   +-- Executar busca
|   +-- Editar nome/descricao
|   +-- Favoritar busca
|   +-- Estatisticas de uso
|
+-- [FUTURO] TAB: MAPEAMENTO (mapping)
+-- [FUTURO] TAB: PERSONAS (personas)
+-- [FUTURO] TAB: PIPELINES (pipelines)
|
+-- MODAIS:
    +-- CandidatePreview (painel lateral)
    +-- CandidatePage (perfil completo)
    +-- NewCandidateUnifiedModal (adicionar candidato)
    +-- AddToListModal (adicionar a lista)
    +-- AddCandidatesToVacancyModal (vincular a vaga)
    +-- AddListToVacanciesModal (vincular lista a vagas)
    +-- UnifiedCommunicationModal (email/whatsapp)
    +-- WSITextScreeningModal (triagem texto)
    +-- WSITriagemInviteModal (convite triagem)
    +-- SendEmailModal (email avulso)
    +-- CVPreview (visualizar CV parseado)
    +-- BatchApprovalModal (aprovacao em lote)
    +-- CandidateReviewModal (review calibracao)
    +-- CandidateComparison (comparar candidatos)
    +-- AdvancedFiltersModal (filtros avancados)
    +-- CreditConfirmationDialog (confirmar creditos)
    +-- RevealCreditsModal (revelar contatos)
    +-- UnsavedPearchWarningModal (aviso candidatos nao salvos)
```

---

## 3. DOCUMENTACAO POR PAGINA/TAB

---

### 3.1 TAB: BUSCA DE CANDIDATOS

#### 3.1.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Busca de Candidatos |
| **Objetivo** | Encontrar candidatos atraves de busca AI-powered em multiplas fontes |
| **Jornada** | Tab principal ao acessar Funil de Talentos |
| **Dependencias** | API Pearch, LIA API, Base local |
| **Dependentes** | Favoritos, Listas, Vagas |

#### 3.1.2 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| BUS-001 | Busca Natural (IA) | Buscar candidatos com linguagem natural |
| BUS-002 | Busca por Perfil Similar | Encontrar perfis semelhantes a um LinkedIn URL |
| BUS-003 | Busca por Job Description | Encontrar candidatos que se encaixam em uma JD |
| BUS-004 | Busca Boolean | Busca com operadores AND/OR/NOT |
| BUS-005 | Busca por Arquetipos | Buscar por perfis pre-definidos de personalidade |
| BUS-006 | Selecionar Fonte | Escolher Local, Global (Pearch) ou Hibrido |
| BUS-007 | Aplicar Filtros Avancados | Filtrar por localizacao, experiencia, senioridade, etc |
| BUS-008 | Ver Resultados em Tabela | Visualizar candidatos em tabela configuravel |
| BUS-009 | Ordenar Resultados | Ordenar por score, nome, empresa, etc |
| BUS-010 | Paginar Resultados | Navegar entre paginas de resultados |
| BUS-011 | Selecionar Candidatos | Checkbox para selecao multipla |
| BUS-012 | Acoes em Lote | Aplicar acoes em candidatos selecionados |
| BUS-013 | Abrir Preview | Ver detalhes do candidato em painel lateral |
| BUS-014 | Abrir Perfil Completo | Ver pagina completa do candidato |
| BUS-015 | Adicionar a Favoritos | Marcar candidato como favorito |
| BUS-016 | Adicionar a Lista | Incluir candidato em uma lista |
| BUS-017 | Vincular a Vaga | Adicionar candidato a uma vaga |
| BUS-018 | Enviar Email | Disparar comunicacao por email |
| BUS-019 | Enviar WhatsApp | Disparar comunicacao por WhatsApp |
| BUS-020 | Iniciar Triagem WSI | Iniciar triagem automatizada |
| BUS-021 | Upload de CV | Fazer upload de CV para parsing |
| BUS-022 | Revelar Contato (Pearch) | Revelar dados de contato pagando creditos |
| BUS-023 | Salvar na Base Local | Salvar candidato Pearch na base local |
| BUS-024 | Expandir para Global | Expandir busca local para incluir Pearch |
| BUS-025 | Salvar Busca | Salvar query atual como busca favorita |
| BUS-026 | Comparar Candidatos | Comparar lado a lado |
| BUS-027 | Ver Insights LIA | Ver sugestoes e analises da LIA |

---

#### BUS-001: Busca Natural (IA)

**Historia de Usuario:**
> "Como recrutador, eu quero buscar candidatos usando linguagem natural para encontrar perfis sem precisar construir queries complexas."

**Regras de Negocio:**
1. O usuario digita em linguagem natural (ex: "Desenvolvedor Python senior em Sao Paulo")
2. A LIA interpreta a query e extrai entidades (skills, localizacao, senioridade)
3. A busca retorna candidatos ordenados por relevancia/match
4. Entidades detectadas sao exibidas como "Context Pills" editaveis
5. Historico da busca e salvo automaticamente

**Inputs:**
- `query` (string) - Texto da busca natural
- `source` (local/global/hybrid) - Fonte de dados
- `filters` (object) - Filtros adicionais

**Outputs:**
- `candidates[]` - Lista de candidatos com scores
- `entities` - Entidades detectadas pela IA
- `metadata` - Informacoes sobre a busca (tempo, total)

**Validacoes:**
- Query nao pode estar vazia
- Minimo 3 caracteres

**Edge Cases:**
- Query muito generica: Exibir aviso e sugerir refinamento
- Nenhum resultado: Sugerir expandir para busca global
- Timeout da IA: Fallback para busca textual simples

---

#### BUS-006: Selecionar Fonte de Busca

**Historia de Usuario:**
> "Como recrutador, eu quero escolher onde buscar candidatos para controlar custos e escopo da busca."

**Regras de Negocio:**
1. Tres opcoes: Local (gratuito), Global (creditos), Hibrido (ambos)
2. Local busca apenas na base da empresa
3. Global busca no Pearch AI (800M+ perfis)
4. Hibrido prioriza local e complementa com global
5. Busca global requer confirmacao de creditos antes de executar
6. Candidatos globais precisam ser "revelados" (pago) para ver contatos

**Calculo de Creditos:**
```
Creditos = num_resultados * 0.10 (estimativa)
Creditos por revelacao = 1 credito/contato
```

**Inputs:**
- `source` (local/global/hybrid)
- `query` (string)

**Outputs:**
- `candidates[]` com `isGlobal` flag
- `creditEstimate` - estimativa de custo

---

### 3.2 TAB: FAVORITOS

#### 3.2.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Favoritos |
| **Objetivo** | Gerenciar candidatos marcados como favoritos pelo recrutador |
| **Jornada** | Atalho para candidatos de interesse |
| **Dependencias** | Base de candidatos |
| **Dependentes** | Nenhum |

#### 3.2.2 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| FAV-001 | Listar Favoritos | Ver todos os candidatos favoritados |
| FAV-002 | Filtrar por Tipo | Filtrar: Todos, Fixados, Com Estrela |
| FAV-003 | Buscar Favorito | Buscar por nome, cargo, skills |
| FAV-004 | Fixar Candidato | Dar destaque a candidatos importantes |
| FAV-005 | Adicionar Nota | Adicionar nota pessoal ao favorito |
| FAV-006 | Editar Nota | Modificar nota existente |
| FAV-007 | Remover Favorito | Remover candidato dos favoritos |
| FAV-008 | Ordenar Favoritos | Ordenar por score, nome, data |
| FAV-009 | Abrir Preview | Ver detalhes do candidato |
| FAV-010 | Ver Analise LIA | Ver parecer da LIA sobre candidato |

---

#### FAV-004: Fixar Candidato

**Historia de Usuario:**
> "Como recrutador, eu quero fixar candidatos prioritarios no topo da lista de favoritos para acessa-los rapidamente."

**Regras de Negocio:**
1. Candidato fixado aparece no topo da lista
2. Multiplos candidatos podem ser fixados
3. Fixados sao ordenados por data de fixacao
4. Icone de pin indica status de fixado
5. Desfixar retorna candidato para lista normal

**Inputs:**
- `candidateId` (string)

**Outputs:**
- `isPinned` (boolean) - status atualizado

---

### 3.3 TAB: LISTAS

#### 3.3.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Listas de Candidatos |
| **Objetivo** | Organizar candidatos em listas personalizadas |
| **Jornada** | Organizacao e segmentacao de candidatos |
| **Dependencias** | Base de candidatos, API Listas |
| **Dependentes** | Vagas (vinculo de listas) |

#### 3.3.2 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| LIS-001 | Listar Listas | Ver todas as listas criadas |
| LIS-002 | Criar Lista | Criar nova lista com nome, descricao e cor |
| LIS-003 | Editar Lista | Modificar nome, descricao ou cor |
| LIS-004 | Excluir Lista | Remover lista (candidatos permanecem) |
| LIS-005 | Buscar Listas | Buscar lista por nome |
| LIS-006 | Ver Candidatos | Abrir lista e ver candidatos |
| LIS-007 | Adicionar Candidato | Incluir candidato na lista |
| LIS-008 | Remover Candidato | Remover candidato da lista |
| LIS-009 | Vincular a Vagas | Associar lista a uma ou mais vagas |
| LIS-010 | Exportar Lista | Exportar candidatos da lista |

---

#### LIS-002: Criar Lista

**Historia de Usuario:**
> "Como recrutador, eu quero criar listas personalizadas para organizar candidatos por projeto, perfil ou qualquer criterio que eu definir."

**Regras de Negocio:**
1. Nome da lista e obrigatorio
2. Descricao e opcional
3. Cor e selecionavel entre 8 opcoes pre-definidas
4. Nao pode haver duas listas com mesmo nome
5. Lista criada aparece no topo da lista
6. Limite de 100 listas por usuario

**Cores Disponiveis:**
```javascript
const LIST_COLORS = [
  { value: '#60BED1', name: 'Cyan' },
  { value: '#6B7280', name: 'Cinza' },
  { value: '#10B981', name: 'Verde' },
  { value: '#F59E0B', name: 'Amarelo' },
  { value: '#EF4444', name: 'Vermelho' },
  { value: '#8B5CF6', name: 'Roxo' },
  { value: '#EC4899', name: 'Rosa' },
  { value: '#3B82F6', name: 'Azul' },
]
```

**Inputs:**
- `name` (string, required)
- `description` (string, optional)
- `color` (string, default: '#60BED1')

**Outputs:**
- `list` - Objeto da lista criada com ID

---

### 3.4 TAB: HISTORICO

#### 3.4.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Historico de Buscas |
| **Objetivo** | Visualizar e reutilizar buscas realizadas anteriormente |
| **Jornada** | Recuperar buscas passadas |
| **Dependencias** | LocalStorage, API History |
| **Dependentes** | Buscas Salvas |

#### 3.4.2 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| HIS-001 | Listar Historico | Ver buscas agrupadas por data |
| HIS-002 | Re-executar Busca | Executar novamente uma busca |
| HIS-003 | Salvar como Favorita | Salvar busca nas Buscas Salvas |
| HIS-004 | Excluir Item | Remover busca do historico |
| HIS-005 | Limpar Historico | Apagar todo o historico |
| HIS-006 | Ver Detalhes | Ver modo, fonte e entidades da busca |

---

#### HIS-002: Re-executar Busca

**Historia de Usuario:**
> "Como recrutador, eu quero re-executar uma busca anterior para ver resultados atualizados sem precisar digitar novamente."

**Regras de Negocio:**
1. Clique no botao "Executar" dispara a busca
2. Parametros originais (modo, fonte, filtros) sao preservados
3. Resultados sao atualizados em tempo real
4. Nova execucao cria entrada no historico
5. Usuario e redirecionado para tab Busca com resultados

**Inputs:**
- `historyItem` - Item do historico com query, mode, source

**Outputs:**
- Redirect para tab Busca
- Resultados da busca atualizados

---

### 3.5 TAB: BUSCAS SALVAS

#### 3.5.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Buscas Salvas |
| **Objetivo** | Gerenciar buscas frequentes salvas pelo usuario |
| **Jornada** | Acesso rapido a buscas recorrentes |
| **Dependencias** | LocalStorage, API Saved Searches |
| **Dependentes** | Nenhum |

#### 3.5.2 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| SAV-001 | Listar Buscas Salvas | Ver todas as buscas salvas |
| SAV-002 | Criar Busca | Salvar nova busca com nome e descricao |
| SAV-003 | Editar Busca | Modificar nome ou descricao |
| SAV-004 | Excluir Busca | Remover busca salva |
| SAV-005 | Executar Busca | Rodar a busca salva |
| SAV-006 | Favoritar Busca | Marcar busca como favorita |
| SAV-007 | Ver Estatisticas | Ver uso: vezes executada, media de resultados |
| SAV-008 | Ordenar Buscas | Ordenar por nome, data, frequencia |

---

## 4. CARDS DE ESPECIFICACAO (JIRA)

---

### CARD BUS-001: Busca Natural com IA

```yaml
Titulo: [FULL-STACK] Implementar Busca Natural com IA
Tipo: Feature
Sprint: 1
Pontos: 13

Descricao: |
  Implementar busca de candidatos usando linguagem natural,
  com interpretacao automatica de entidades pela LIA.

Historia de Usuario: |
  Como recrutador, eu quero buscar candidatos usando linguagem
  natural para encontrar perfis sem precisar construir queries complexas.

Regras de Negocio:
  1. Input aceita texto livre em portugues
  2. LIA extrai entidades: skills, localizacao, senioridade, experiencia
  3. Entidades exibidas como pills editaveis
  4. Resultados ordenados por score de match
  5. Historico salvo automaticamente
  6. Sugestoes de refinamento se poucos resultados

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/search
    - Integracao com Claude API para NLP
    - Cache de resultados por 5 minutos
    - Rate limiting: 10 req/min
  Frontend:
    - SmartSearchInput component (Vue/Vuetify)
    - Context Pills para entidades
    - Loading animation durante busca
    - Debounce de 300ms no input
  Dados:
    - search_history: query, mode, source, entities, timestamp
    - candidates: campos indexados para busca
  IA:
    - Claude Sonnet para entity extraction
    - Prompt template para parsing de query
    - Fallback para busca textual se IA falhar
  Integracoes:
    - LIA Backend API
    - Pearch API (se fonte global)

Riscos:
  - Latencia da IA pode ser alta (>3s)
  - Custo de API Claude por query
  - Precisao da extracao de entidades

DoD (Definition of Done):
  - [ ] Input aceita texto natural
  - [ ] Entidades sao extraidas corretamente
  - [ ] Pills sao editaveis
  - [ ] Resultados ordenados por relevancia
  - [ ] Historico salvo
  - [ ] Loading state funciona
  - [ ] Testes unitarios passando
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Busca por "Dev Python SP" retorna devs Python em SP
  - [ ] Entidades skill=Python, location=SP detectadas
  - [ ] Tempo de resposta < 5 segundos
  - [ ] Erro exibe mensagem amigavel
```

---

### CARD LIS-002: Criar Lista de Candidatos

```yaml
Titulo: [FULL-STACK] CRUD de Listas de Candidatos
Tipo: Feature
Sprint: 2
Pontos: 8

Descricao: |
  Implementar criacao, edicao e exclusao de listas personalizadas
  para organizacao de candidatos.

Historia de Usuario: |
  Como recrutador, eu quero criar listas personalizadas para
  organizar candidatos por projeto ou criterio.

Regras de Negocio:
  1. Nome obrigatorio, descricao opcional
  2. Cor selecionavel (8 opcoes)
  3. Nomes unicos por usuario
  4. Limite de 100 listas
  5. Excluir lista nao exclui candidatos

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/candidate-lists
    - POST /api/v1/candidate-lists
    - PUT /api/v1/candidate-lists/{id}
    - DELETE /api/v1/candidate-lists/{id}
    - Validacao de unicidade de nome
  Frontend:
    - ListsTab component (Vue/Vuetify)
    - Modal de criacao/edicao
    - Dialog de confirmacao para exclusao
    - Toast de feedback
  Dados:
    - candidate_lists: id, name, description, color, user_id, created_at
    - candidate_list_items: list_id, candidate_id
  Integracoes:
    - N/A

Riscos:
  - Listas grandes podem impactar performance
  - Conflito de nomes entre usuarios

DoD:
  - [ ] CRUD completo funcionando
  - [ ] Validacoes de backend
  - [ ] UI responsiva
  - [ ] Testes passando

Criterios de Aceitacao:
  - [ ] Criar lista com nome e cor
  - [ ] Editar nome e descricao
  - [ ] Excluir lista (candidatos permanecem)
  - [ ] Erro ao criar nome duplicado
```

---

### CARD FAV-001: Sistema de Favoritos

```yaml
Titulo: [FULL-STACK] Implementar Sistema de Favoritos com Notas
Tipo: Feature
Sprint: 2
Pontos: 5

Descricao: |
  Sistema de favoritos com opcao de fixar candidatos e adicionar
  notas pessoais para cada favorito.

Historia de Usuario: |
  Como recrutador, eu quero marcar candidatos como favoritos
  e adicionar notas para lembrar por que os selecionei.

Regras de Negocio:
  1. Toggle de favorito (estrela)
  2. Toggle de fixado (pin)
  3. Nota opcional (texto livre)
  4. Fixados aparecem no topo
  5. Persistencia no backend e localStorage

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/{id}/favorite
    - PUT /api/v1/candidates/{id}/favorite
    - DELETE /api/v1/candidates/{id}/favorite
    - GET /api/v1/candidates/favorites
  Frontend:
    - FavoritesTab component
    - Popover para nota
    - Filtros: todos/fixados/favoritos
    - Ordenacao por score/nome/data
  Dados:
    - candidate_favorites: candidate_id, user_id, note, is_pinned, created_at
  Integracoes:
    - Sync com localStorage como fallback

Riscos:
  - Conflito de dados localStorage vs API

DoD:
  - [ ] Favoritar/desfavoritar funciona
  - [ ] Fixar/desfixar funciona
  - [ ] Notas salvas e exibidas
  - [ ] Filtros funcionam
  - [ ] Testes passando

Criterios de Aceitacao:
  - [ ] Clicar na estrela favorita/desfavorita
  - [ ] Clicar no pin fixa/desfixa
  - [ ] Nota salva ao clicar fora do popover
  - [ ] Fixados aparecem no topo
```

---

## 5. DIAGRAMAS DE JORNADA

### 5.1 Jornada: Buscar e Salvar Candidato em Lista

```
PONTO DE VISTA DO USUARIO:

INICIO
  +-- Recrutador acessa Funil de Talentos
       +-- Digita "Desenvolvedor React 5 anos SP"
            +-- LIA mostra entidades detectadas
                 +-- Seleciona fonte "Local"
                      +-- Clica em "Buscar"
                           +-- Resultados aparecem na tabela
                                +-- Seleciona 3 candidatos (checkbox)
                                     +-- Clica em "Adicionar a Lista"
                                          +-- Escolhe lista "Projeto X"
                                               +-- Toast confirma adicao
FIM

PONTO DE VISTA DO SISTEMA:

[FRONT] Usuario digita query no SmartSearchInput
[IA] LIA API recebe query para entity extraction
[IA] Claude processa e retorna entities: {skill: "React", experience: 5, location: "SP"}
[FRONT] Exibe Context Pills com entidades
[FRONT] Usuario confirma e clica buscar
[FRONT] Chama API com loading state
[BACK] POST /api/v1/candidates/search
[BACK] Query no banco local com filtros
[DADOS] SELECT * FROM candidates WHERE skills LIKE '%React%' AND location = 'SP' AND experience >= 5
[BACK] Calcula scores e ordena
[BACK] Retorna lista paginada
[FRONT] Renderiza tabela com resultados
[FRONT] Usuario seleciona candidatos
[FRONT] Clica em "Adicionar a Lista"
[FRONT] Abre AddToListModal
[FRONT] Usuario seleciona lista
[BACK] POST /api/v1/candidate-lists/{id}/candidates
[DADOS] INSERT INTO candidate_list_items (list_id, candidate_id) VALUES ...
[BACK] Retorna sucesso
[FRONT] Fecha modal
[FRONT] Exibe toast de sucesso
```

### 5.2 Jornada: Busca Global com Revelacao de Contato

```
PONTO DE VISTA DO USUARIO:

INICIO
  +-- Recrutador seleciona fonte "Global (Pearch)"
       +-- Sistema mostra estimativa de creditos
            +-- Confirma busca
                 +-- Resultados globais aparecem (sem contatos)
                      +-- Clica em "Revelar Contato" em um candidato
                           +-- Confirma uso de 1 credito
                                +-- Email e telefone aparecem
                                     +-- Candidato e salvo na base local
FIM

PONTO DE VISTA DO SISTEMA:

[FRONT] Usuario seleciona source = 'global'
[FRONT] Chama API para estimar creditos
[BACK] GET /api/v1/pearch/estimate?query=...
[INTEGRACOES] Pearch API retorna estimativa
[FRONT] Exibe CreditConfirmationDialog
[FRONT] Usuario confirma
[BACK] POST /api/v1/candidates/search (source=global)
[INTEGRACOES] Pearch API executa busca
[BACK] Retorna candidatos com dados parciais (sem contatos)
[FRONT] Renderiza tabela com badge "Global"
[FRONT] Usuario clica "Revelar Contato"
[FRONT] Abre RevealCreditsModal
[FRONT] Usuario confirma
[BACK] POST /api/v1/pearch/reveal/{pearch_id}
[INTEGRACOES] Pearch API retorna dados completos
[BACK] Debita credito da conta
[DADOS] INSERT INTO candidates (dados completos do Pearch)
[DADOS] INSERT INTO credit_transactions
[BACK] Retorna candidato com contatos
[FRONT] Atualiza card com dados revelados
[FRONT] Toast confirma revelacao
```

---

## 6. ROADMAP POR FASES

### FASE 1: FUNDACAO (Sprint 1-2)

```
PRIORIDADE ALTA
+-- [BACK] API de busca de candidatos local
|   +-- GET/POST /api/v1/candidates/search
+-- [BACK] CRUD de listas de candidatos
|   +-- /api/v1/candidate-lists/*
+-- [BACK] API de favoritos
|   +-- /api/v1/candidates/{id}/favorite
+-- [FRONT] SmartSearchInput component
|   +-- Input com modos de busca
+-- [FRONT] UnifiedCandidateTable
|   +-- Tabela configuravel de resultados
+-- [FRONT] ListsTab component
+-- [FRONT] FavoritesTab component
+-- [DADOS] Modelos: candidates, lists, favorites, search_history

PRIORIDADE MEDIA
+-- [FRONT] CandidatePreview (painel lateral)
+-- [FRONT] Filtros basicos de busca
+-- [IA] Entity extraction com Claude
```

### FASE 2: INTELIGENCIA (Sprint 3-4)

```
PRIORIDADE ALTA
+-- [IA] Busca Natural com NLP
|   +-- Integracao Claude para parsing
+-- [FRONT] Context Pills editaveis
+-- [FRONT] HistoryTab com re-execucao
+-- [FRONT] SavedSearchesTab com estatisticas
+-- [BACK] API de historico e buscas salvas
+-- [INTEGRACOES] Integracao Pearch AI (busca global)

PRIORIDADE MEDIA
+-- [FRONT] AdvancedFiltersModal
+-- [FRONT] Upload e parsing de CV
+-- [IA] Sugestoes de refinamento
```

### FASE 3: INTEGRACAO (Sprint 5-6)

```
PRIORIDADE ALTA
+-- [INTEGRACOES] Revelacao de contatos Pearch
+-- [BACK] Sistema de creditos
+-- [FRONT] CreditConfirmationDialog
+-- [FRONT] RevealCreditsModal
+-- [FRONT] AddToVacancyModal
+-- [BACK] Vinculo candidatos-vagas

PRIORIDADE MEDIA
+-- [FRONT] Comparacao de candidatos
+-- [FRONT] Bulk actions
+-- [IA] Analise LIA de candidatos
```

### FASE 4: AVANCADO (Sprint 7-8)

```
PRIORIDADE MEDIA
+-- [FRONT] Tab Mapeamento (estrutura de mercado)
+-- [FRONT] Tab Personas (perfis ideais)
+-- [FRONT] Tab Pipelines (workflows customizados)
+-- [IA] Arquetipos de busca
+-- [DADOS] Analytics de sourcing

PRIORIDADE BAIXA
+-- [FRONT] Exportacao de candidatos
+-- [FRONT] Import de candidatos via planilha
+-- [IA] Calibracao de busca
```

---

## 7. PADROES DE DESIGN

### 7.1 Paleta de Cores

```css
/* Fundo Principal */
--bg-main: #F9FAFB;           /* Cinza quase branco */
--bg-card: #FFFFFF;           /* Cards */

/* Texto */
--text-primary: #1F2937;      /* Titulos (gray-800) */
--text-secondary: #4B5563;    /* Corpo (gray-600) */
--text-tertiary: #6B7280;     /* Labels (gray-500) */

/* Destaque Principal */
--accent-primary: #60BED1;    /* Ciano WeDo */

/* Cores de Modo de Busca */
--mode-natural: #8B5CF6;      /* Roxo - Sparkles */
--mode-similar: #3B82F6;      /* Azul - Users */
--mode-jd: #10B981;           /* Verde - FileText */
--mode-boolean: #F59E0B;      /* Amarelo - Binary */
--mode-archetypes: #EC4899;   /* Rosa - Target */

/* Cores de Fonte */
--source-local: #6B7280;      /* Cinza - Database */
--source-global: #3B82F6;     /* Azul - Cloud */
--source-hybrid: #8B5CF6;     /* Roxo - Sparkles */

/* Badges */
--badge-success: #DCFCE7;     /* Verde claro */
--badge-warning: #FEF3C7;     /* Amarelo claro */
--badge-error: #FEE2E2;       /* Vermelho claro */
--badge-info: #DBEAFE;        /* Azul claro */
```

### 7.2 Componentes: Tailwind para Vuetify

| Componente | Tailwind (Prototipo) | Vuetify 3 (Producao) |
|------------|---------------------|---------------------|
| Tabs | Custom com border-bottom | `<v-tabs>` com `<v-tab>` |
| Tabela | Custom table com CSS | `<v-data-table>` |
| Input busca | `<Input>` + icons | `<v-text-field>` com prepend/append |
| Chips/Pills | `<Badge>` custom | `<v-chip>` |
| Modal | Radix Dialog | `<v-dialog>` |
| Dropdown | Radix DropdownMenu | `<v-menu>` com `<v-list>` |
| Toggle/Switch | `<Switch>` | `<v-switch>` |
| Card de candidato | Custom Card | `<v-card>` |
| Avatar | `<Avatar>` | `<v-avatar>` |
| Tooltip | Radix Tooltip | `<v-tooltip>` |
| Loading | Custom spinner | `<v-progress-circular>` |
| Toast | useToast hook | `<v-snackbar>` |

---

## 8. USO DE IA

### 8.1 Pontos de IA no Funil de Talentos

| Ponto | Onde Entra | O que Recebe | O que Devolve | Modelo/Agent |
|-------|------------|--------------|---------------|--------------|
| Entity Extraction | SmartSearchInput | Query texto natural | {skills, location, experience, seniority} | Claude Sonnet |
| Busca Semantica | Backend Search | Query + entities | Candidatos rankeados por match | Embeddings + Claude |
| Analise de Perfil | CandidatePreview | Dados do candidato | Score LIA, Big Five, parecer | Claude Sonnet |
| CV Parsing | Upload CV | Arquivo PDF/DOCX | Dados estruturados do candidato | Claude Sonnet |
| Sugestoes de Refinamento | Resultados vazios | Query original | Queries alternativas | Claude Sonnet |
| Matching JD-Candidato | Busca por JD | Job Description + candidato | Fit score 0-100 | Claude Sonnet |
| Geracao de Arquetipos | Arquetipos | Descricao do perfil ideal | Persona com Big Five | Claude Sonnet |

### 8.2 Riscos e Mitigacoes

| Risco | Impacto | Mitigacao |
|-------|---------|-----------|
| Latencia IA (>5s) | UX ruim | Cache de resultados, loading animado, streaming |
| Custo API Claude | Budget | Rate limiting, cache agressivo, fallback textual |
| Extracao incorreta | Resultados errados | Pills editaveis, confirmacao do usuario |
| Vies algoritmico | Discriminacao | Auditoria, regras anti-vies, diversidade |
| Dados sensiveis no prompt | Privacidade | Anonimizacao, nao enviar dados pessoais |

### 8.3 Fallbacks

```yaml
Se IA nao responder em 10s:
  - Exibir loading com mensagem
  - Tentar fallback para busca textual simples
  - Logar erro para analise

Se entity extraction falhar:
  - Usar query completa como busca textual
  - Exibir aviso: "Busca simplificada"
  - Sugerir usar modo Boolean

Se Pearch nao responder:
  - Exibir apenas resultados locais
  - Notificar usuario
  - Botao para tentar novamente
```

---

## 9. REQUISITOS FUNCIONAIS

### 9.1 Requisitos de Busca
1. O sistema deve permitir busca por linguagem natural
2. O sistema deve suportar 5 modos de busca: Natural, Similar, JD, Boolean, Arquetipos
3. O sistema deve permitir selecao de fonte: Local, Global, Hibrido
4. O sistema deve extrair entidades automaticamente da query
5. O sistema deve exibir entidades como pills editaveis
6. O sistema deve salvar historico de buscas automaticamente
7. O sistema deve permitir re-executar buscas do historico
8. O sistema deve permitir salvar buscas como favoritas
9. O sistema deve exibir estimativa de creditos para busca global
10. O sistema deve permitir filtros avancados (localizacao, experiencia, etc)

### 9.2 Requisitos de Resultados
11. O sistema deve exibir resultados em tabela configuravel
12. O sistema deve permitir ordenar por qualquer coluna
13. O sistema deve permitir paginar resultados (50/100/200 por pagina)
14. O sistema deve permitir selecao multipla de candidatos
15. O sistema deve exibir preview lateral do candidato
16. O sistema deve diferenciar visualmente candidatos locais e globais

### 9.3 Requisitos de Organizacao
17. O sistema deve permitir criar/editar/excluir listas de candidatos
18. O sistema deve permitir adicionar candidatos a listas
19. O sistema deve permitir favoritar candidatos com notas
20. O sistema deve permitir fixar candidatos favoritos
21. O sistema deve permitir vincular listas a vagas
22. O sistema deve permitir vincular candidatos individuais a vagas

### 9.4 Requisitos de Integracao
23. O sistema deve integrar com Pearch AI para busca global
24. O sistema deve permitir revelar contatos pagando creditos
25. O sistema deve salvar candidatos globais na base local
26. O sistema deve enviar emails e WhatsApp diretamente
27. O sistema deve iniciar triagem WSI de candidatos

---

## 10. LISTA DE TASKS IMPORTAVEL

```csv
Titulo,Descricao,Tipo,Dependencias,Criterios de Aceitacao,Estimativa Ideal,Estimativa Realista,Estimativa Pessimista
[BACK] API Busca Local Candidatos,Endpoint de busca com filtros e ordenacao,feature,,Retorna lista paginada com scores,4h,6h,10h
[BACK] API Entity Extraction,Integracao Claude para extrair entidades de query,feature,API Busca,Retorna entities: skills location experience,4h,6h,10h
[BACK] CRUD Listas de Candidatos,Endpoints para criar editar excluir listas,feature,,CRUD completo funcionando,3h,5h,8h
[BACK] API Adicionar Candidato a Lista,Endpoint para vincular candidato a lista,feature,CRUD Listas,Adiciona e retorna sucesso,2h,3h,5h
[BACK] API Favoritos com Notas,Endpoints para favoritar/fixar com notas,feature,,Toggle e notas funcionando,3h,5h,8h
[BACK] API Historico de Buscas,Endpoints para listar e gerenciar historico,feature,,CRUD historico funcionando,2h,4h,6h
[BACK] API Buscas Salvas,Endpoints para salvar e executar buscas,feature,API Historico,CRUD buscas salvas funcionando,3h,5h,8h
[BACK] Integracao Pearch Search,Conectar API Pearch para busca global,feature,,Busca global retorna resultados,6h,10h,16h
[BACK] Integracao Pearch Reveal,Revelar contatos com debito de creditos,feature,Integracao Pearch,Contatos revelados e salvos,4h,6h,10h
[BACK] API Vincular Candidatos a Vaga,Endpoint para adicionar candidatos a vaga,feature,,Candidatos vinculados a vaga,3h,5h,8h
[FRONT] SmartSearchInput Component,Input AI-powered com modos de busca,feature,,Input com 5 modos funcionando,6h,10h,16h
[FRONT] Context Pills Editaveis,Pills para entidades detectadas,feature,SmartSearchInput,Pills editaveis e removiveis,4h,6h,10h
[FRONT] Seletor de Fonte Busca,Toggle Local/Global/Hibrido,feature,SmartSearchInput,Fonte selecionavel,2h,3h,5h
[FRONT] UnifiedCandidateTable,Tabela de resultados configuravel,feature,,Tabela com ordenacao e paginacao,8h,12h,20h
[FRONT] CandidatePreview Panel,Painel lateral com preview do candidato,feature,UnifiedCandidateTable,Preview abre e fecha,6h,10h,16h
[FRONT] FavoritesTab Component,Tab de favoritos com filtros,feature,API Favoritos,Lista e filtra favoritos,5h,8h,12h
[FRONT] ListsTab Component,Tab de listas com CRUD,feature,CRUD Listas,Cria edita exclui listas,6h,10h,16h
[FRONT] HistoryTab Component,Tab de historico com re-execucao,feature,API Historico,Lista e re-executa buscas,5h,8h,12h
[FRONT] SavedSearchesTab Component,Tab de buscas salvas,feature,API Buscas Salvas,Lista e executa buscas salvas,5h,8h,12h
[FRONT] AddToListModal,Modal para adicionar candidatos a lista,feature,ListsTab,Seleciona lista e adiciona,3h,5h,8h
[FRONT] AddToVacancyModal,Modal para vincular candidatos a vaga,feature,,Seleciona vaga e vincula,4h,6h,10h
[FRONT] CreditConfirmationDialog,Dialog de confirmacao de creditos Pearch,feature,Integracao Pearch,Exibe creditos e confirma,2h,3h,5h
[FRONT] RevealCreditsModal,Modal para revelar contatos,feature,Pearch Reveal,Revela e exibe contatos,3h,5h,8h
[IA] NLP Pipeline Busca Natural,Pipeline completo de busca com IA,feature,Entity Extraction,Busca natural funciona ponta a ponta,8h,12h,20h
[IA] CV Parsing com Claude,Upload e parsing de CV,feature,,CV parseado para dados estruturados,6h,10h,16h
[IA] Sugestoes de Refinamento,Sugerir queries quando poucos resultados,feature,NLP Pipeline,Sugestoes aparecem,4h,6h,10h
[DADOS] Modelo search_history,Tabela para historico de buscas,tech debt,,Modelo criado e migrado,1h,2h,3h
[DADOS] Modelo saved_searches,Tabela para buscas salvas,tech debt,,Modelo criado e migrado,1h,2h,3h
[DADOS] Modelo candidate_favorites,Tabela para favoritos com notas,tech debt,,Modelo criado e migrado,1h,2h,3h
[DADOS] Modelo candidate_lists,Tabelas para listas de candidatos,tech debt,,Modelos criados e migrados,2h,3h,5h
[TEST] Testes Unitarios Busca,Testes para componentes de busca,tech debt,Componentes Busca,Cobertura > 80%,4h,6h,10h
[TEST] Testes E2E Fluxo Busca,Teste do fluxo completo de busca e salvar,tech debt,Componentes,Fluxo passa sem erros,4h,6h,10h
[DOCS] Documentacao API Funil,Swagger/OpenAPI para endpoints,tech debt,APIs Backend,Endpoints documentados,3h,4h,6h
```

---

## APENDICE: PERGUNTAS EM ABERTO

1. **Limites de Listas:** Qual o limite maximo de listas por usuario?
2. **Limites de Candidatos por Lista:** Existe limite de candidatos em uma lista?
3. **Creditos Pearch:** Como funciona o sistema de creditos? Renovacao mensal?
4. **Retencao de Historico:** Por quanto tempo manter historico de buscas?
5. **Export:** Quais formatos de export sao necessarios (CSV, Excel, PDF)?
6. **Tab Mapeamento:** Qual a funcionalidade exata desta tab?
7. **Tab Personas:** Como funcionam os arquetipos personalizados?
8. **Tab Pipelines:** Qual a diferenca para o Kanban de vagas?
9. **Permissoes:** Diferentes niveis de acesso (visualizar vs editar)?
10. **Compartilhamento:** Listas podem ser compartilhadas entre usuarios?

---

*Documento gerado com base na analise do codigo-fonte do prototipo.*
*Arquivo: plataforma-lia/src/components/pages/candidates-page.tsx*
*Tabs: plataforma-lia/src/components/talent-funnel-tabs/*
