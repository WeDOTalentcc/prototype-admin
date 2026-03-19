# CARDS JIRA - FUNIL DE TALENTOS (COMPLETO)

> **Total de Cards:** 69 cards (61 frontend/full-stack + 8 backend IA)  
> **Organizacao:** Por Tab/Funcionalidade  
> **Data:** Dezembro 2024  
> **Atualizado:** 22 Janeiro 2026 - Cards IA implementados + contexto de stack

---

## CONTEXTO DE USO DOS CARDS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AMBIENTE ATUAL (Prototipo/Referencia)    →    AMBIENTE PRODUCAO (Time)    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FRONTEND                                                                   │
│  plataforma-lia/                               Stack Producao:              │
│  ├── Next.js + React + TypeScript      →       ├── Vue.js + Vuetify         │
│  ├── Tailwind CSS + shadcn/ui                  ├── Nuxt.js                  │
│  └── Drizzle ORM                               └── CSS Framework            │
│                                                                              │
│  BACKEND CRUD/API                                                           │
│  (Endpoints REST para CRUD de candidatos)      Stack Producao:              │
│  ├── Python + FastAPI                  →       ├── Ruby on Rails 7          │
│  └── SQLAlchemy                                └── ActiveRecord             │
│                                                                              │
│  BACKEND IA (MESMO STACK)                                                   │
│  lia-agent-system/                             Stack Producao:              │
│  ├── Python + FastAPI                  =       ├── Python + FastAPI         │
│  ├── LangGraph + Gemini/Claude                 ├── LangGraph + Gemini/Claude│
│  └── Agentes Especializados                    └── Agentes Especializados   │
│                                                                              │
│  PROPOSITO: Estes cards servem como ESPECIFICACAO para o time              │
│  replicar as funcionalidades no stack de producao.                         │
│                                                                              │
│  STATUS DOS CARDS:                                                          │
│  • "Implementado" = Funcional aqui, pronto para replicar/usar              │
│  • "Pendente" = Ainda nao replicado no stack de producao                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## INDICE DE CARDS

### TAB BUSCA (27 cards)
- BUS-001 a BUS-027

### TAB FAVORITOS (10 cards)
- FAV-001 a FAV-010

### TAB LISTAS (10 cards)
- LIS-001 a LIS-010

### TAB HISTORICO (6 cards)
- HIS-001 a HIS-006

### TAB BUSCAS SALVAS (8 cards)
- SAV-001 a SAV-008

### BACKEND IA (8 cards) - NOVO
- FUN-IA-001 a FUN-IA-008

---

## TAB BUSCA - CARDS JIRA

---

### CARD BUS-001: Busca Natural com IA

```yaml
Titulo: [FULL-STACK] Implementar Busca Natural com IA
Tipo: Feature
Sprint: 1
Pontos: 13
Prioridade: Alta

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

### CARD BUS-002: Busca por Perfil Similar

```yaml
Titulo: [FULL-STACK] Implementar Busca por Perfil Similar
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta

Descricao: |
  Permitir buscar candidatos similares a um perfil de referencia
  usando URL do LinkedIn ou candidato existente na base.

Historia de Usuario: |
  Como recrutador, eu quero encontrar candidatos similares a um
  perfil que ja conheco para expandir meu pipeline.

Regras de Negocio:
  1. Aceita URL do LinkedIn como input
  2. Aceita ID de candidato da base como referencia
  3. Extrai caracteristicas do perfil de referencia
  4. Busca candidatos com perfil similar
  5. Ordena por grau de similaridade

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/search/similar
    - Scraping/API LinkedIn para extrair dados
    - Algoritmo de similaridade (skills, experiencia, senioridade)
  Frontend:
    - Input para URL ou seletor de candidato
    - Preview do perfil de referencia
    - Indicador de similaridade nos resultados
  IA:
    - Embeddings para calculo de similaridade
    - Match de skills e experiencia

DoD:
  - [ ] Input de URL funciona
  - [ ] Seletor de candidato funciona
  - [ ] Resultados ordenados por similaridade
  - [ ] Score de similaridade exibido

Criterios de Aceitacao:
  - [ ] URL do LinkedIn retorna perfil
  - [ ] Candidatos similares sao encontrados
  - [ ] Similaridade calculada corretamente
```

---

### CARD BUS-003: Busca por Job Description

```yaml
Titulo: [FULL-STACK] Implementar Busca por Job Description
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta

Descricao: |
  Permitir colar uma descricao de vaga e encontrar candidatos
  que se encaixam nos requisitos descritos.

Historia de Usuario: |
  Como recrutador, eu quero colar uma descricao de vaga e
  encontrar candidatos compativeis automaticamente.

Regras de Negocio:
  1. Textarea para colar JD completa
  2. LIA extrai requisitos da JD
  3. Match candidatos com requisitos
  4. Score de fit calculado
  5. Destaque de requisitos atendidos

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/search/jd
    - Parsing de JD com Claude
    - Algoritmo de matching
  Frontend:
    - Textarea expansivel para JD
    - Preview de requisitos extraidos
    - Score de fit por candidato
  IA:
    - Extracao de requisitos (skills, experiencia, soft skills)
    - Matching semantico

DoD:
  - [ ] Textarea aceita JD
  - [ ] Requisitos extraidos corretamente
  - [ ] Match calculado
  - [ ] Score de fit exibido

Criterios de Aceitacao:
  - [ ] JD parseada em requisitos
  - [ ] Candidatos ordenados por fit
  - [ ] Requisitos atendidos destacados
```

---

### CARD BUS-004: Busca Boolean

```yaml
Titulo: [FRONTEND] Implementar Busca Boolean
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Permitir buscas usando operadores booleanos
  (AND, OR, NOT, parenteses).

Historia de Usuario: |
  Como recrutador experiente, eu quero usar operadores booleanos
  para construir buscas precisas e complexas.

Regras de Negocio:
  1. Suportar AND, OR, NOT
  2. Suportar parenteses para agrupamento
  3. Suportar aspas para termos exatos
  4. Validacao de sintaxe em tempo real
  5. Sugestoes de autocomplete

Requisitos Tecnicos:
  Backend:
    - Parser de query boolean
    - Traducao para query SQL/ElasticSearch
  Frontend:
    - Input com syntax highlighting
    - Validacao em tempo real
    - Ajuda de sintaxe

DoD:
  - [ ] Operadores funcionam
  - [ ] Parenteses funcionam
  - [ ] Aspas funcionam
  - [ ] Validacao funciona

Criterios de Aceitacao:
  - [ ] "Python AND React" funciona
  - [ ] "(Python OR Java) AND Senior" funciona
  - [ ] Erro de sintaxe exibe mensagem
```

---

### CARD BUS-005: Busca por Arquetipos

```yaml
Titulo: [FULL-STACK] Implementar Busca por Arquetipos
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Media

Descricao: |
  Permitir buscar candidatos por arquetipos de personalidade
  pre-definidos baseados no Big Five.

Historia de Usuario: |
  Como recrutador, eu quero buscar por perfis comportamentais
  para encontrar candidatos com fit cultural.

Regras de Negocio:
  1. Lista de arquetipos pre-definidos
  2. Possibilidade de criar arquetipos custom
  3. Match baseado em Big Five
  4. Score de fit comportamental
  5. Arquetipos sao salvos por usuario

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/archetypes
    - POST /api/v1/archetypes (custom)
    - Algoritmo de match Big Five
  Frontend:
    - Grid de arquetipos com icones
    - Modal de criacao de arquetipo
    - Slider para tracos Big Five
  IA:
    - Geracao de arquetipo a partir de descricao

DoD:
  - [ ] Lista de arquetipos exibida
  - [ ] Busca por arquetipo funciona
  - [ ] Criacao de arquetipo custom funciona
  - [ ] Match Big Five calculado

Criterios de Aceitacao:
  - [ ] Arquetipos padrao disponiveis
  - [ ] Arquetipo custom pode ser criado
  - [ ] Candidatos ordenados por fit
```

---

### CARD BUS-006: Selecionar Fonte de Busca

```yaml
Titulo: [FRONTEND] Implementar Seletor de Fonte de Busca
Tipo: Feature
Sprint: 1
Pontos: 3
Prioridade: Alta

Descricao: |
  Toggle para selecionar fonte de busca: Local, Global ou Hibrido.

Historia de Usuario: |
  Como recrutador, eu quero escolher onde buscar candidatos
  para controlar custos e escopo da busca.

Regras de Negocio:
  1. Tres opcoes: Local, Global (Pearch), Hibrido
  2. Local e gratuito
  3. Global consome creditos
  4. Hibrido prioriza local e complementa com global
  5. Persistir ultima escolha

Requisitos Tecnicos:
  Frontend:
    - ToggleGroup com 3 opcoes
    - Icones: Database, Cloud, Sparkles
    - Tooltip explicando cada opcao
    - Persist em localStorage

DoD:
  - [ ] Toggle funciona
  - [ ] Icones corretos
  - [ ] Tooltips informativos
  - [ ] Persistencia funciona

Criterios de Aceitacao:
  - [ ] Clicar alterna entre fontes
  - [ ] Fonte selecionada e usada na busca
  - [ ] Escolha persiste entre sessoes
```

---

### CARD BUS-007: Aplicar Filtros Avancados

```yaml
Titulo: [FRONTEND] Implementar Modal de Filtros Avancados
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta

Descricao: |
  Modal com filtros avancados para refinar resultados de busca.

Historia de Usuario: |
  Como recrutador, eu quero aplicar filtros avancados para
  encontrar candidatos mais especificos.

Regras de Negocio:
  1. Filtro por localizacao (cidade, estado, pais)
  2. Filtro por experiencia (anos)
  3. Filtro por senioridade (junior, pleno, senior)
  4. Filtro por modelo de trabalho (remoto, hibrido, presencial)
  5. Filtro por faixa salarial
  6. Filtro por skills especificas
  7. Filtro por idiomas
  8. Filtros combinaveis

Requisitos Tecnicos:
  Frontend:
    - AdvancedFiltersModal component
    - Inputs: autocomplete, slider, checkbox
    - Contador de filtros ativos
    - Botao limpar filtros
  Backend:
    - Suporte a todos os filtros na API

DoD:
  - [ ] Modal abre e fecha
  - [ ] Todos os filtros funcionam
  - [ ] Filtros combinaveis
  - [ ] Contador atualiza
  - [ ] Limpar funciona

Criterios de Aceitacao:
  - [ ] Filtrar por SP retorna candidatos de SP
  - [ ] Filtrar por 5+ anos retorna seniors
  - [ ] Combinar filtros funciona
```

---

### CARD BUS-008: Exibir Resultados em Tabela

```yaml
Titulo: [FRONTEND] Implementar UnifiedCandidateTable
Tipo: Feature
Sprint: 1
Pontos: 13
Prioridade: Alta

Descricao: |
  Tabela configuravel para exibir resultados de busca de candidatos.

Historia de Usuario: |
  Como recrutador, eu quero ver resultados em uma tabela
  organizada e configuravel.

Regras de Negocio:
  1. Colunas: Nome, Score, Cargo, Empresa, Local, Skills, Acoes
  2. Colunas podem ser ocultadas/exibidas
  3. Colunas podem ser reordenadas
  4. Colunas podem ser redimensionadas
  5. Linha clicavel abre preview
  6. Checkbox para selecao multipla
  7. Hover destaca linha

Requisitos Tecnicos:
  Frontend:
    - v-data-table (Vuetify) ou custom
    - Drag & drop de colunas
    - Resize de colunas
    - Persist config em localStorage
  Performance:
    - Virtualizacao para listas grandes
    - Lazy loading de imagens

DoD:
  - [ ] Tabela renderiza candidatos
  - [ ] Colunas configuraveis
  - [ ] Reordenacao funciona
  - [ ] Resize funciona
  - [ ] Selecao funciona

Criterios de Aceitacao:
  - [ ] 100 candidatos renderizam em <1s
  - [ ] Config de colunas persiste
  - [ ] Clique abre preview
```

---

### CARD BUS-009: Ordenar Resultados

```yaml
Titulo: [FRONTEND] Implementar Ordenacao de Resultados
Tipo: Feature
Sprint: 1
Pontos: 3
Prioridade: Alta

Descricao: |
  Permitir ordenar resultados por qualquer coluna.

Historia de Usuario: |
  Como recrutador, eu quero ordenar candidatos por score
  para ver os melhores primeiro.

Regras de Negocio:
  1. Clique no header ordena
  2. Clique duplo inverte ordem
  3. Icone indica direcao (asc/desc)
  4. Ordenacao padrao: score desc
  5. Multi-sort opcional

Requisitos Tecnicos:
  Frontend:
    - Sort icons nos headers
    - Estado de ordenacao
    - Animacao de transicao

DoD:
  - [ ] Clique ordena
  - [ ] Icone atualiza
  - [ ] Multi-sort funciona

Criterios de Aceitacao:
  - [ ] Ordenar por score funciona
  - [ ] Ordenar por nome funciona
  - [ ] Inverter ordem funciona
```

---

### CARD BUS-010: Paginar Resultados

```yaml
Titulo: [FRONTEND] Implementar Paginacao de Resultados
Tipo: Feature
Sprint: 1
Pontos: 3
Prioridade: Alta

Descricao: |
  Paginacao para navegar entre paginas de resultados.

Historia de Usuario: |
  Como recrutador, eu quero navegar entre paginas de resultados
  quando houver muitos candidatos.

Regras de Negocio:
  1. Opcoes: 25, 50, 100, 200 por pagina
  2. Navegacao: primeira, anterior, proxima, ultima
  3. Input para ir a pagina especifica
  4. Exibir: "Mostrando X-Y de Z candidatos"

Requisitos Tecnicos:
  Frontend:
    - v-pagination (Vuetify)
    - Select para items por pagina
    - Info de range

DoD:
  - [ ] Navegacao funciona
  - [ ] Items por pagina funciona
  - [ ] Info atualiza

Criterios de Aceitacao:
  - [ ] Mudar pagina atualiza tabela
  - [ ] Mudar items por pagina funciona
  - [ ] Range exibido corretamente
```

---

### CARD BUS-011: Selecionar Candidatos

```yaml
Titulo: [FRONTEND] Implementar Selecao Multipla de Candidatos
Tipo: Feature
Sprint: 1
Pontos: 3
Prioridade: Alta

Descricao: |
  Checkbox para selecionar multiplos candidatos para acoes em lote.

Historia de Usuario: |
  Como recrutador, eu quero selecionar varios candidatos
  para aplicar acoes em lote.

Regras de Negocio:
  1. Checkbox por linha
  2. Checkbox no header seleciona todos da pagina
  3. Contador de selecionados
  4. Selecao persiste entre paginas
  5. Banner de acoes aparece quando ha selecao

Requisitos Tecnicos:
  Frontend:
    - v-checkbox em cada linha
    - Estado global de selecao
    - ContextualActionsBanner

DoD:
  - [ ] Checkbox funciona
  - [ ] Selecionar todos funciona
  - [ ] Contador atualiza
  - [ ] Banner aparece

Criterios de Aceitacao:
  - [ ] Selecionar 5 candidatos exibe banner
  - [ ] Selecionar todos seleciona pagina inteira
  - [ ] Deselecionar funciona
```

---

### CARD BUS-012: Acoes em Lote

```yaml
Titulo: [FULL-STACK] Implementar Acoes em Lote
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Media

Descricao: |
  Aplicar acoes em multiplos candidatos selecionados.

Historia de Usuario: |
  Como recrutador, eu quero aplicar acoes em varios candidatos
  de uma vez para ganhar produtividade.

Regras de Negocio:
  1. Acoes disponiveis: Adicionar a lista, Adicionar a vaga, 
     Enviar email, Favoritar, Revelar contatos
  2. Confirmacao antes de executar
  3. Progresso exibido durante execucao
  4. Relatorio de sucesso/falha ao final

Requisitos Tecnicos:
  Backend:
    - Endpoints de batch para cada acao
    - Processamento assincrono para grandes volumes
  Frontend:
    - Dropdown de acoes no banner
    - Modal de confirmacao
    - Progress bar
    - Toast de resultado

DoD:
  - [ ] Todas as acoes funcionam
  - [ ] Confirmacao exibida
  - [ ] Progresso atualiza
  - [ ] Relatorio final exibido

Criterios de Aceitacao:
  - [ ] Adicionar 10 candidatos a lista funciona
  - [ ] Enviar email para 5 candidatos funciona
  - [ ] Erros sao reportados
```

---

### CARD BUS-013: Abrir Preview do Candidato

```yaml
Titulo: [FRONTEND] Implementar CandidatePreview Panel
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta

Descricao: |
  Painel lateral com preview do candidato selecionado.

Historia de Usuario: |
  Como recrutador, eu quero ver detalhes de um candidato
  sem sair da lista de resultados.

Regras de Negocio:
  1. Clique na linha abre preview lateral
  2. Preview exibe: foto, nome, cargo, empresa, skills, 
     experiencia, formacao, score LIA
  3. Painel redimensionavel
  4. Setas para navegar entre candidatos
  5. Botao para maximizar/fechar
  6. Acoes rapidas: favoritar, email, whatsapp

Requisitos Tecnicos:
  Frontend:
    - Painel com transicao suave
    - Resize handle
    - Navegacao por teclado (setas)
    - Scroll interno

DoD:
  - [ ] Preview abre ao clicar
  - [ ] Dados exibidos corretamente
  - [ ] Resize funciona
  - [ ] Navegacao funciona
  - [ ] Acoes funcionam

Criterios de Aceitacao:
  - [ ] Clicar em candidato abre preview
  - [ ] Setas navegam para proximo/anterior
  - [ ] Redimensionar persiste
```

---

### CARD BUS-014: Abrir Perfil Completo

```yaml
Titulo: [FRONTEND] Implementar CandidatePage Modal
Tipo: Feature
Sprint: 3
Pontos: 13
Prioridade: Media

Descricao: |
  Modal de tela cheia com perfil completo do candidato.

Historia de Usuario: |
  Como recrutador, eu quero ver todas as informacoes de um
  candidato em uma pagina dedicada.

Regras de Negocio:
  1. Botao "Maximizar" no preview abre modal
  2. Tabs: Resumo, Experiencia, Formacao, Skills, Parecer LIA
  3. Timeline de experiencia profissional
  4. Graficos de skills e Big Five
  5. Historico de interacoes
  6. Acoes completas disponiveis

Requisitos Tecnicos:
  Frontend:
    - v-dialog fullscreen
    - Tabs para navegacao
    - Charts para visualizacoes
    - Timeline component

DoD:
  - [ ] Modal abre em fullscreen
  - [ ] Todas as tabs funcionam
  - [ ] Dados carregam corretamente
  - [ ] Acoes funcionam

Criterios de Aceitacao:
  - [ ] Todos os dados do candidato exibidos
  - [ ] Graficos renderizam
  - [ ] Historico de interacoes visivel
```

---

### CARD BUS-015: Adicionar a Favoritos

```yaml
Titulo: [FRONTEND] Implementar Toggle de Favorito
Tipo: Feature
Sprint: 1
Pontos: 2
Prioridade: Alta

Descricao: |
  Botao para favoritar/desfavoritar candidato.

Historia de Usuario: |
  Como recrutador, eu quero marcar candidatos como favoritos
  para acessa-los rapidamente depois.

Regras de Negocio:
  1. Icone de estrela toggle
  2. Animacao ao favoritar
  3. Sincroniza com backend e localStorage
  4. Candidato aparece na tab Favoritos

Requisitos Tecnicos:
  Frontend:
    - Icone Star com animacao
    - Optimistic update
    - Fallback para localStorage
  Backend:
    - POST /api/v1/candidates/{id}/favorite

DoD:
  - [ ] Toggle funciona
  - [ ] Animacao suave
  - [ ] Sincroniza com backend
  - [ ] Aparece em Favoritos

Criterios de Aceitacao:
  - [ ] Clicar na estrela favorita
  - [ ] Clicar novamente desfavorita
  - [ ] Candidato aparece na tab Favoritos
```

---

### CARD BUS-016: Adicionar a Lista

```yaml
Titulo: [FRONTEND] Implementar AddToListModal
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Modal para adicionar candidato(s) a uma lista existente ou nova.

Historia de Usuario: |
  Como recrutador, eu quero adicionar candidatos a listas
  para organiza-los por projeto ou criterio.

Regras de Negocio:
  1. Listar listas existentes do usuario
  2. Opcao de criar nova lista inline
  3. Busca/filtro de listas
  4. Multiplos candidatos podem ser adicionados
  5. Toast de confirmacao

Requisitos Tecnicos:
  Frontend:
    - v-dialog com lista de listas
    - Input para busca
    - Botao criar nova lista
    - Loading state
  Backend:
    - POST /api/v1/candidate-lists/{id}/candidates

DoD:
  - [ ] Modal abre
  - [ ] Listas carregam
  - [ ] Adicionar funciona
  - [ ] Criar nova funciona

Criterios de Aceitacao:
  - [ ] Selecionar lista e adicionar candidato
  - [ ] Criar nova lista e adicionar
  - [ ] Adicionar multiplos candidatos
```

---

### CARD BUS-017: Vincular a Vaga

```yaml
Titulo: [FRONTEND] Implementar AddToVacancyModal
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Modal para vincular candidato(s) a uma vaga.

Historia de Usuario: |
  Como recrutador, eu quero adicionar candidatos a uma vaga
  para iniciar o processo seletivo.

Regras de Negocio:
  1. Listar vagas abertas da empresa
  2. Busca/filtro de vagas
  3. Exibir estagio inicial (Funil)
  4. Multiplos candidatos podem ser vinculados
  5. Detectar se candidato ja esta na vaga

Requisitos Tecnicos:
  Frontend:
    - v-dialog com lista de vagas
    - Input para busca
    - Badge de vagas por status
    - Aviso de duplicata
  Backend:
    - POST /api/v1/jobs/{id}/candidates

DoD:
  - [ ] Modal abre
  - [ ] Vagas carregam
  - [ ] Vincular funciona
  - [ ] Duplicata detectada

Criterios de Aceitacao:
  - [ ] Selecionar vaga e vincular candidato
  - [ ] Candidato aparece no Kanban da vaga
  - [ ] Aviso se ja esta na vaga
```

---

### CARD BUS-018: Enviar Email

```yaml
Titulo: [FRONTEND] Implementar Acao de Enviar Email
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Abrir modal de envio de email para candidato.

Historia de Usuario: |
  Como recrutador, eu quero enviar email para um candidato
  diretamente da plataforma.

Regras de Negocio:
  1. Botao "Email" abre modal de comunicacao
  2. Pre-preenche destinatario
  3. Templates disponiveis
  4. Personalizacao de mensagem
  5. Historico de envios registrado

Requisitos Tecnicos:
  Frontend:
    - Botao abre UnifiedCommunicationModal
    - Tipo: 'email'
    - Pre-fill do candidato
  Backend:
    - POST /api/v1/communications

DoD:
  - [ ] Botao abre modal
  - [ ] Candidato pre-preenchido
  - [ ] Templates carregam
  - [ ] Envio funciona

Criterios de Aceitacao:
  - [ ] Modal abre com email do candidato
  - [ ] Selecionar template funciona
  - [ ] Enviar registra no historico
```

---

### CARD BUS-019: Enviar WhatsApp

```yaml
Titulo: [FRONTEND] Implementar Acao de Enviar WhatsApp
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Abrir modal de envio de mensagem WhatsApp para candidato.

Historia de Usuario: |
  Como recrutador, eu quero enviar WhatsApp para um candidato
  diretamente da plataforma.

Regras de Negocio:
  1. Botao "WhatsApp" abre modal de comunicacao
  2. Pre-preenche numero
  3. Templates disponiveis
  4. Personalizacao de mensagem
  5. Abre WhatsApp Web ou app

Requisitos Tecnicos:
  Frontend:
    - Botao abre UnifiedCommunicationModal
    - Tipo: 'whatsapp'
    - Link wa.me ou API WhatsApp Business

DoD:
  - [ ] Botao abre modal
  - [ ] Numero pre-preenchido
  - [ ] Templates carregam
  - [ ] Abre WhatsApp

Criterios de Aceitacao:
  - [ ] Modal abre com numero do candidato
  - [ ] Selecionar template funciona
  - [ ] Clicar enviar abre WhatsApp
```

---

### CARD BUS-020: Iniciar Triagem WSI

```yaml
Titulo: [FULL-STACK] Implementar Acao de Triagem WSI
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Media

Descricao: |
  Iniciar processo de triagem automatizada WSI para candidato.

Historia de Usuario: |
  Como recrutador, eu quero iniciar uma triagem automatizada
  para avaliar candidatos rapidamente.

Regras de Negocio:
  1. Botao "Triagem" abre modal WSI
  2. Selecionar tipo: texto ou voz
  3. Selecionar vaga de referencia
  4. Enviar convite ao candidato
  5. Aguardar respostas

Requisitos Tecnicos:
  Frontend:
    - WSITriagemInviteModal
    - Selecao de vaga
    - Selecao de tipo
  Backend:
    - POST /api/v1/screenings
    - Integracao com agente WSI

DoD:
  - [ ] Modal abre
  - [ ] Tipos disponiveis
  - [ ] Vagas listadas
  - [ ] Convite enviado

Criterios de Aceitacao:
  - [ ] Iniciar triagem texto funciona
  - [ ] Iniciar triagem voz funciona
  - [ ] Candidato recebe convite
```

---

### CARD BUS-021: Upload de CV

```yaml
Titulo: [FULL-STACK] Implementar Upload e Parsing de CV
Tipo: Feature
Sprint: 3
Pontos: 13
Prioridade: Media

Descricao: |
  Upload de CV com parsing automatico por IA.

Historia de Usuario: |
  Como recrutador, eu quero fazer upload de um CV e ter os
  dados extraidos automaticamente.

Regras de Negocio:
  1. Drag & drop ou click para upload
  2. Formatos: PDF, DOCX, DOC
  3. Parsing com Claude AI
  4. Preview de dados extraidos
  5. Edicao manual antes de salvar
  6. Criar candidato na base

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/parse-cv
    - Integracao Claude para parsing
    - Armazenamento de arquivo
  Frontend:
    - Dropzone component
    - Preview de dados
    - Form de edicao
  IA:
    - Prompt template para extracao
    - Campos: nome, email, telefone, skills, experiencia

DoD:
  - [ ] Upload funciona
  - [ ] Parsing extrai dados
  - [ ] Preview exibe dados
  - [ ] Edicao funciona
  - [ ] Candidato criado

Criterios de Aceitacao:
  - [ ] Upload de PDF funciona
  - [ ] Nome e email extraidos
  - [ ] Skills identificadas
  - [ ] Candidato salvo na base
```

---

### CARD BUS-022: Revelar Contato Pearch

```yaml
Titulo: [FULL-STACK] Implementar Revelacao de Contatos Pearch
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Media

Descricao: |
  Revelar dados de contato de candidatos da busca global (Pearch)
  consumindo creditos.

Historia de Usuario: |
  Como recrutador, eu quero revelar o email e telefone de um
  candidato global para poder contat-lo.

Regras de Negocio:
  1. Candidatos Pearch nao tem contato visivel
  2. Botao "Revelar" exibe custo em creditos
  3. Confirmacao antes de debitar
  4. Contatos revelados sao exibidos
  5. Candidato e salvo na base local

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/pearch/reveal/{pearch_id}
    - Debito de creditos
    - Salvamento na base local
  Frontend:
    - Botao com custo
    - Modal de confirmacao
    - Animacao de revelacao

DoD:
  - [ ] Botao exibe custo
  - [ ] Confirmacao funciona
  - [ ] Contatos revelados
  - [ ] Creditos debitados
  - [ ] Candidato salvo

Criterios de Aceitacao:
  - [ ] Revelar mostra email e telefone
  - [ ] Credito debitado corretamente
  - [ ] Candidato aparece na base local
```

---

### CARD BUS-023: Salvar na Base Local

```yaml
Titulo: [FULL-STACK] Implementar Salvamento de Candidato Pearch
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media

Descricao: |
  Salvar candidato da busca global na base local da empresa.

Historia de Usuario: |
  Como recrutador, eu quero salvar candidatos globais na minha
  base para poder trabalh-los depois.

Regras de Negocio:
  1. Botao "Salvar na Base" para candidatos Pearch
  2. Dados parciais salvos (sem contato se nao revelado)
  3. Candidato fica disponivel em buscas locais
  4. Badge indica origem Pearch

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/save-pearch
    - Mapeamento de campos Pearch -> local
  Frontend:
    - Botao de salvar
    - Badge de origem
    - Toast de confirmacao

DoD:
  - [ ] Botao funciona
  - [ ] Candidato salvo
  - [ ] Badge exibido
  - [ ] Aparece em busca local

Criterios de Aceitacao:
  - [ ] Salvar candidato Pearch funciona
  - [ ] Origem Pearch mantida
  - [ ] Busca local encontra candidato
```

---

### CARD BUS-024: Expandir para Busca Global

```yaml
Titulo: [FRONTEND] Implementar Expansao de Busca para Global
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media

Descricao: |
  Sugerir expansao para busca global quando resultados locais
  sao insuficientes.

Historia de Usuario: |
  Como recrutador, eu quero expandir minha busca para a base
  global quando nao encontro candidatos locais.

Regras de Negocio:
  1. Se <10 resultados locais, sugerir expansao
  2. Exibir estimativa de creditos
  3. Um clique para expandir
  4. Manter filtros aplicados

Requisitos Tecnicos:
  Frontend:
    - Banner de sugestao
    - Botao de expansao
    - CreditConfirmationDialog

DoD:
  - [ ] Banner aparece com poucos resultados
  - [ ] Botao expande busca
  - [ ] Creditos estimados
  - [ ] Filtros mantidos

Criterios de Aceitacao:
  - [ ] Sugestao aparece com <10 resultados
  - [ ] Expandir adiciona resultados globais
  - [ ] Confirmacao de creditos exibida
```

---

### CARD BUS-025: Salvar Busca

```yaml
Titulo: [FRONTEND] Implementar Salvar Busca Atual
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media

Descricao: |
  Salvar a busca atual como busca favorita para reutilizacao.

Historia de Usuario: |
  Como recrutador, eu quero salvar buscas frequentes para
  nao precisar digita-las novamente.

Regras de Negocio:
  1. Botao "Salvar Busca" na area de resultados
  2. Modal para nome e descricao
  3. Query, modo, fonte e filtros salvos
  4. Aparece na tab Buscas Salvas

Requisitos Tecnicos:
  Frontend:
    - Botao com icone Bookmark
    - Modal com form
    - Toast de confirmacao
  Backend:
    - POST /api/v1/saved-searches

DoD:
  - [ ] Botao funciona
  - [ ] Modal abre
  - [ ] Busca salva
  - [ ] Aparece em Buscas Salvas

Criterios de Aceitacao:
  - [ ] Salvar com nome funciona
  - [ ] Query e filtros preservados
  - [ ] Busca aparece na tab
```

---

### CARD BUS-026: Comparar Candidatos

```yaml
Titulo: [FRONTEND] Implementar Comparacao de Candidatos
Tipo: Feature
Sprint: 5
Pontos: 8
Prioridade: Baixa

Descricao: |
  Modal para comparar 2-4 candidatos lado a lado.

Historia de Usuario: |
  Como recrutador, eu quero comparar candidatos lado a lado
  para tomar decisoes mais informadas.

Regras de Negocio:
  1. Selecionar 2-4 candidatos
  2. Botao "Comparar" no banner de acoes
  3. Modal com colunas lado a lado
  4. Comparar: skills, experiencia, score, salario
  5. Destaque de diferencas

Requisitos Tecnicos:
  Frontend:
    - CandidateComparison component
    - Layout de colunas
    - Highlight de diferencas
    - Scroll sincronizado

DoD:
  - [ ] Selecionar candidatos funciona
  - [ ] Modal abre
  - [ ] Dados comparados
  - [ ] Diferencas destacadas

Criterios de Aceitacao:
  - [ ] Comparar 2 candidatos funciona
  - [ ] Comparar 4 candidatos funciona
  - [ ] Destaque visual de diferencas
```

---

### CARD BUS-027: Ver Insights LIA

```yaml
Titulo: [FRONTEND] Implementar Painel de Insights LIA
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Baixa

Descricao: |
  Painel lateral com sugestoes e insights da LIA sobre a busca.

Historia de Usuario: |
  Como recrutador, eu quero ver sugestoes da LIA para melhorar
  minha busca ou entender os resultados.

Regras de Negocio:
  1. Painel colapsavel na lateral
  2. Sugestoes de refinamento
  3. Insights sobre os resultados
  4. Acoes rapidas sugeridas
  5. Perguntas frequentes

Requisitos Tecnicos:
  Frontend:
    - Painel expansivel
    - Cards de sugestoes
    - Quick actions
  IA:
    - Analise de resultados
    - Geracao de sugestoes

DoD:
  - [ ] Painel abre e fecha
  - [ ] Sugestoes carregam
  - [ ] Acoes funcionam

Criterios de Aceitacao:
  - [ ] Insights relevantes exibidos
  - [ ] Clicar em sugestao aplica
  - [ ] Painel nao atrapalha tabela
```

---

## TAB FAVORITOS - CARDS JIRA

---

### CARD FAV-001: Listar Favoritos

```yaml
Titulo: [FRONTEND] Implementar Lista de Favoritos
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Exibir todos os candidatos marcados como favoritos pelo usuario.

Historia de Usuario: |
  Como recrutador, eu quero ver todos os meus candidatos
  favoritos em uma lista dedicada.

Regras de Negocio:
  1. Listar todos os favoritos do usuario
  2. Ordenar por data de adicao (mais recente primeiro)
  3. Exibir nota se houver
  4. Exibir se esta fixado
  5. Acoes rapidas disponiveis

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/candidates/favorites
  Frontend:
    - FavoritesTab component
    - UnifiedCandidateTable
    - Coluna de nota

DoD:
  - [ ] Lista carrega
  - [ ] Ordenacao funciona
  - [ ] Notas exibidas
  - [ ] Pins exibidos

Criterios de Aceitacao:
  - [ ] Todos os favoritos listados
  - [ ] Mais recentes primeiro
  - [ ] Notas visiveis
```

---

### CARD FAV-002: Filtrar por Tipo

```yaml
Titulo: [FRONTEND] Implementar Filtros de Favoritos
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Filtrar favoritos por tipo: Todos, Fixados, Com Estrela.

Historia de Usuario: |
  Como recrutador, eu quero filtrar meus favoritos para
  encontrar rapidamente os mais importantes.

Regras de Negocio:
  1. Filtro: Todos (padrao)
  2. Filtro: Fixados (pins)
  3. Filtro: Com Estrela (favoritos sem pin)
  4. Contador por tipo

Requisitos Tecnicos:
  Frontend:
    - ToggleGroup de filtros
    - Contadores por tipo
    - Filtro local (client-side)

DoD:
  - [ ] Toggle funciona
  - [ ] Contadores corretos
  - [ ] Filtro aplica

Criterios de Aceitacao:
  - [ ] Filtrar fixados mostra apenas fixados
  - [ ] Contadores atualizados
```

---

### CARD FAV-003: Buscar Favorito

```yaml
Titulo: [FRONTEND] Implementar Busca em Favoritos
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Buscar favoritos por nome, cargo ou skills.

Historia de Usuario: |
  Como recrutador, eu quero buscar entre meus favoritos
  para encontrar rapidamente um candidato.

Regras de Negocio:
  1. Input de busca no topo
  2. Busca por nome, cargo, skills
  3. Busca em tempo real (debounce)
  4. Destacar termo encontrado

Requisitos Tecnicos:
  Frontend:
    - Input de busca
    - Filtro client-side
    - Debounce 300ms

DoD:
  - [ ] Input funciona
  - [ ] Busca filtra
  - [ ] Highlight funciona

Criterios de Aceitacao:
  - [ ] Buscar "Python" filtra candidatos com Python
  - [ ] Buscar nome encontra candidato
```

---

### CARD FAV-004: Fixar Candidato

```yaml
Titulo: [FRONTEND] Implementar Fixar Candidato
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Alta

Descricao: |
  Fixar candidatos favoritos no topo da lista.

Historia de Usuario: |
  Como recrutador, eu quero fixar candidatos prioritarios
  no topo para acessa-los rapidamente.

Regras de Negocio:
  1. Icone de pin por candidato
  2. Toggle de fixar/desfixar
  3. Fixados aparecem no topo
  4. Ordenacao entre fixados por data

Requisitos Tecnicos:
  Frontend:
    - Icone Pin
    - Toggle state
    - Ordenacao local
  Backend:
    - PUT /api/v1/candidates/{id}/favorite (is_pinned)

DoD:
  - [ ] Pin toggle funciona
  - [ ] Fixados no topo
  - [ ] Ordenacao correta

Criterios de Aceitacao:
  - [ ] Clicar no pin fixa
  - [ ] Candidato vai para o topo
  - [ ] Clicar novamente desfixa
```

---

### CARD FAV-005: Adicionar Nota

```yaml
Titulo: [FRONTEND] Implementar Notas em Favoritos
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media

Descricao: |
  Adicionar nota pessoal a um candidato favorito.

Historia de Usuario: |
  Como recrutador, eu quero adicionar notas aos favoritos
  para lembrar por que os selecionei.

Regras de Negocio:
  1. Icone de nota por candidato
  2. Popover com textarea
  3. Salvar ao clicar fora
  4. Exibir preview da nota na lista

Requisitos Tecnicos:
  Frontend:
    - Icone StickyNote
    - Popover com textarea
    - Blur handler para salvar
  Backend:
    - PUT /api/v1/candidates/{id}/favorite (note)

DoD:
  - [ ] Popover abre
  - [ ] Nota salva ao fechar
  - [ ] Preview exibido

Criterios de Aceitacao:
  - [ ] Adicionar nota funciona
  - [ ] Nota visivel na lista
  - [ ] Nota salva no backend
```

---

### CARD FAV-006: Editar Nota

```yaml
Titulo: [FRONTEND] Implementar Edicao de Nota
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Editar nota existente de um favorito.

Historia de Usuario: |
  Como recrutador, eu quero editar notas de favoritos
  para mante-las atualizadas.

Regras de Negocio:
  1. Clicar na nota abre popover
  2. Texto atual pre-preenchido
  3. Salvar ao clicar fora
  4. Botao para limpar nota

Requisitos Tecnicos:
  Frontend:
    - Popover editavel
    - Pre-fill
    - Botao limpar

DoD:
  - [ ] Edicao funciona
  - [ ] Pre-fill correto
  - [ ] Limpar funciona

Criterios de Aceitacao:
  - [ ] Editar nota existente
  - [ ] Limpar nota
```

---

### CARD FAV-007: Remover Favorito

```yaml
Titulo: [FRONTEND] Implementar Remover Favorito
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Alta

Descricao: |
  Remover candidato dos favoritos.

Historia de Usuario: |
  Como recrutador, eu quero remover candidatos dos favoritos
  quando nao sao mais relevantes.

Regras de Negocio:
  1. Clicar na estrela desfavorita
  2. Confirmacao opcional (config)
  3. Candidato removido da lista
  4. Acao reversivel (toast com undo)

Requisitos Tecnicos:
  Frontend:
    - Toggle de estrela
    - Toast com undo
    - Animacao de remocao
  Backend:
    - DELETE /api/v1/candidates/{id}/favorite

DoD:
  - [ ] Toggle funciona
  - [ ] Candidato removido
  - [ ] Undo funciona

Criterios de Aceitacao:
  - [ ] Clicar na estrela remove
  - [ ] Undo restaura favorito
```

---

### CARD FAV-008: Ordenar Favoritos

```yaml
Titulo: [FRONTEND] Implementar Ordenacao de Favoritos
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Ordenar lista de favoritos por diferentes criterios.

Historia de Usuario: |
  Como recrutador, eu quero ordenar favoritos por score
  para ver os melhores primeiro.

Regras de Negocio:
  1. Ordenar por: Data, Score, Nome
  2. Direcao: Asc/Desc
  3. Fixados sempre no topo
  4. Persistir preferencia

Requisitos Tecnicos:
  Frontend:
    - Dropdown de ordenacao
    - Toggle de direcao
    - LocalStorage para persistencia

DoD:
  - [ ] Dropdown funciona
  - [ ] Ordenacao aplica
  - [ ] Fixados no topo
  - [ ] Preferencia salva

Criterios de Aceitacao:
  - [ ] Ordenar por score funciona
  - [ ] Fixados permanecem no topo
```

---

### CARD FAV-009: Abrir Preview

```yaml
Titulo: [FRONTEND] Implementar Preview de Favorito
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Alta

Descricao: |
  Abrir preview do candidato favorito.

Historia de Usuario: |
  Como recrutador, eu quero ver detalhes de um favorito
  sem sair da lista.

Regras de Negocio:
  1. Clicar na linha abre preview
  2. Mesmo CandidatePreview da busca
  3. Navegacao entre favoritos

Requisitos Tecnicos:
  Frontend:
    - Reutilizar CandidatePreview
    - Navegacao por setas

DoD:
  - [ ] Clique abre preview
  - [ ] Navegacao funciona

Criterios de Aceitacao:
  - [ ] Preview abre com dados
  - [ ] Setas navegam entre favoritos
```

---

### CARD FAV-010: Ver Analise LIA

```yaml
Titulo: [FRONTEND] Implementar Analise LIA em Favoritos
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Ver analise da LIA sobre candidato favorito.

Historia de Usuario: |
  Como recrutador, eu quero ver o parecer da LIA sobre
  meus candidatos favoritos.

Regras de Negocio:
  1. Botao "LIA" abre painel de analise
  2. Score LIA, Big Five, parecer
  3. Comparacao com perfil ideal (se houver)

Requisitos Tecnicos:
  Frontend:
    - Painel ou modal de analise
    - Graficos Big Five
    - Parecer textual

DoD:
  - [ ] Botao funciona
  - [ ] Analise carrega
  - [ ] Graficos exibem

Criterios de Aceitacao:
  - [ ] Score LIA visivel
  - [ ] Big Five em grafico
  - [ ] Parecer legivel
```

---

## TAB LISTAS - CARDS JIRA

---

### CARD LIS-001: Listar Listas

```yaml
Titulo: [FRONTEND] Implementar Lista de Listas
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Exibir todas as listas de candidatos criadas pelo usuario.

Historia de Usuario: |
  Como recrutador, eu quero ver todas as minhas listas
  de candidatos em um so lugar.

Regras de Negocio:
  1. Exibir todas as listas do usuario
  2. Card por lista com: nome, cor, contagem, data
  3. Ordenar por ultima atualizacao
  4. Acoes: abrir, editar, excluir

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/candidate-lists
  Frontend:
    - Grid de cards
    - Loading state

DoD:
  - [ ] Listas carregam
  - [ ] Cards exibem info
  - [ ] Ordenacao funciona

Criterios de Aceitacao:
  - [ ] Todas as listas exibidas
  - [ ] Contagem de candidatos correta
```

---

### CARD LIS-002: Criar Lista

```yaml
Titulo: [FULL-STACK] Implementar Criacao de Lista
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Criar nova lista de candidatos com nome, descricao e cor.

Historia de Usuario: |
  Como recrutador, eu quero criar listas para organizar
  candidatos por projeto ou criterio.

Regras de Negocio:
  1. Botao "Nova Lista" abre modal
  2. Nome obrigatorio (unico)
  3. Descricao opcional
  4. Cor selecionavel (8 opcoes)
  5. Lista criada aparece no topo

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidate-lists
    - Validacao de unicidade
  Frontend:
    - Modal com form
    - Color picker
    - Validacao

DoD:
  - [ ] Modal abre
  - [ ] Form valida
  - [ ] Lista criada
  - [ ] Aparece na lista

Criterios de Aceitacao:
  - [ ] Criar lista com nome funciona
  - [ ] Erro se nome duplicado
  - [ ] Cor aplicada
```

---

### CARD LIS-003: Editar Lista

```yaml
Titulo: [FULL-STACK] Implementar Edicao de Lista
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media

Descricao: |
  Editar nome, descricao ou cor de uma lista existente.

Historia de Usuario: |
  Como recrutador, eu quero editar minhas listas para
  mante-las organizadas.

Regras de Negocio:
  1. Botao "Editar" no card/menu
  2. Modal pre-preenchido
  3. Validacao de unicidade de nome
  4. Atualizar imediatamente

Requisitos Tecnicos:
  Backend:
    - PUT /api/v1/candidate-lists/{id}
  Frontend:
    - Modal reutilizado
    - Pre-fill

DoD:
  - [ ] Modal abre pre-preenchido
  - [ ] Edicao salva
  - [ ] Lista atualizada

Criterios de Aceitacao:
  - [ ] Editar nome funciona
  - [ ] Editar cor funciona
```

---

### CARD LIS-004: Excluir Lista

```yaml
Titulo: [FULL-STACK] Implementar Exclusao de Lista
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media

Descricao: |
  Excluir uma lista de candidatos.

Historia de Usuario: |
  Como recrutador, eu quero excluir listas que nao preciso mais.

Regras de Negocio:
  1. Botao "Excluir" no menu
  2. Confirmacao obrigatoria
  3. Candidatos NAO sao excluidos
  4. Acao irreversivel

Requisitos Tecnicos:
  Backend:
    - DELETE /api/v1/candidate-lists/{id}
    - Soft delete ou hard delete
  Frontend:
    - AlertDialog de confirmacao
    - Toast de sucesso

DoD:
  - [ ] Confirmacao exibida
  - [ ] Lista excluida
  - [ ] Candidatos mantidos

Criterios de Aceitacao:
  - [ ] Excluir lista funciona
  - [ ] Candidatos permanecem na base
```

---

### CARD LIS-005: Buscar Listas

```yaml
Titulo: [FRONTEND] Implementar Busca de Listas
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Buscar listas por nome.

Historia de Usuario: |
  Como recrutador, eu quero buscar minhas listas por nome
  quando tenho muitas.

Regras de Negocio:
  1. Input de busca no topo
  2. Filtro por nome e descricao
  3. Busca em tempo real

Requisitos Tecnicos:
  Frontend:
    - Input de busca
    - Filtro client-side
    - Debounce

DoD:
  - [ ] Input funciona
  - [ ] Filtro aplica

Criterios de Aceitacao:
  - [ ] Buscar "Projeto X" encontra lista
```

---

### CARD LIS-006: Ver Candidatos da Lista

```yaml
Titulo: [FRONTEND] Implementar Visualizacao de Candidatos da Lista
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Abrir lista e ver candidatos contidos nela.

Historia de Usuario: |
  Como recrutador, eu quero ver os candidatos de uma lista
  especifica.

Regras de Negocio:
  1. Clicar na lista abre detalhe
  2. Tabela de candidatos da lista
  3. Mesmo layout da busca
  4. Acoes disponiveis

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/candidate-lists/{id}
  Frontend:
    - View de detalhe
    - UnifiedCandidateTable
    - Breadcrumb para voltar

DoD:
  - [ ] Lista abre
  - [ ] Candidatos carregam
  - [ ] Acoes funcionam

Criterios de Aceitacao:
  - [ ] Clicar na lista mostra candidatos
  - [ ] Voltar para listas funciona
```

---

### CARD LIS-007: Adicionar Candidato a Lista

```yaml
Titulo: [FULL-STACK] Implementar Adicao de Candidato a Lista
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta

Descricao: |
  Adicionar candidato(s) a uma lista.

Historia de Usuario: |
  Como recrutador, eu quero adicionar candidatos as minhas
  listas para organiza-los.

Regras de Negocio:
  1. Botao "Adicionar" na busca
  2. Modal de selecao de lista
  3. Multiplos candidatos
  4. Detectar duplicatas

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidate-lists/{id}/candidates
    - Upsert para evitar duplicatas
  Frontend:
    - AddToListModal
    - Multi-select

DoD:
  - [ ] Modal funciona
  - [ ] Candidato adicionado
  - [ ] Duplicata detectada

Criterios de Aceitacao:
  - [ ] Adicionar 1 candidato funciona
  - [ ] Adicionar 5 candidatos funciona
  - [ ] Aviso se ja esta na lista
```

---

### CARD LIS-008: Remover Candidato da Lista

```yaml
Titulo: [FULL-STACK] Implementar Remocao de Candidato da Lista
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media

Descricao: |
  Remover candidato de uma lista.

Historia de Usuario: |
  Como recrutador, eu quero remover candidatos de listas
  quando nao sao mais relevantes.

Regras de Negocio:
  1. Botao "Remover" na linha do candidato
  2. Confirmacao opcional
  3. Candidato removido da lista (nao da base)
  4. Undo disponivel

Requisitos Tecnicos:
  Backend:
    - DELETE /api/v1/candidate-lists/{id}/candidates/{cid}
  Frontend:
    - Botao de remover
    - Toast com undo

DoD:
  - [ ] Remover funciona
  - [ ] Candidato permanece na base
  - [ ] Undo funciona

Criterios de Aceitacao:
  - [ ] Remover candidato da lista
  - [ ] Candidato ainda existe na base
```

---

### CARD LIS-009: Vincular Lista a Vagas

```yaml
Titulo: [FULL-STACK] Implementar Vinculo de Lista a Vagas
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Vincular todos os candidatos de uma lista a uma ou mais vagas.

Historia de Usuario: |
  Como recrutador, eu quero vincular uma lista inteira a uma
  vaga para adicionar varios candidatos de uma vez.

Regras de Negocio:
  1. Botao "Vincular a Vagas" no menu da lista
  2. Modal de selecao de vagas (multi)
  3. Todos os candidatos da lista adicionados
  4. Detectar duplicatas

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/jobs/{id}/candidates/batch
  Frontend:
    - AddListToVacanciesModal
    - Multi-select de vagas

DoD:
  - [ ] Modal funciona
  - [ ] Vagas selecionaveis
  - [ ] Candidatos vinculados
  - [ ] Duplicatas tratadas

Criterios de Aceitacao:
  - [ ] Vincular lista a 1 vaga funciona
  - [ ] Vincular lista a 3 vagas funciona
```

---

### CARD LIS-010: Exportar Lista

```yaml
Titulo: [FULL-STACK] Implementar Exportacao de Lista
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Baixa

Descricao: |
  Exportar candidatos de uma lista para CSV/Excel.

Historia de Usuario: |
  Como recrutador, eu quero exportar listas para compartilhar
  com colegas ou usar em outras ferramentas.

Regras de Negocio:
  1. Botao "Exportar" no menu da lista
  2. Formatos: CSV, Excel
  3. Colunas selecionaveis
  4. Download imediato

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/candidate-lists/{id}/export
    - Geracao de arquivo
  Frontend:
    - Modal de opcoes
    - Download trigger

DoD:
  - [ ] Modal funciona
  - [ ] CSV gerado
  - [ ] Excel gerado
  - [ ] Download funciona

Criterios de Aceitacao:
  - [ ] Exportar CSV com dados corretos
  - [ ] Exportar Excel funciona
```

---

## TAB HISTORICO - CARDS JIRA

---

### CARD HIS-001: Listar Historico

```yaml
Titulo: [FRONTEND] Implementar Lista de Historico
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Exibir historico de buscas realizadas agrupadas por data.

Historia de Usuario: |
  Como recrutador, eu quero ver meu historico de buscas
  para reutilizar queries anteriores.

Regras de Negocio:
  1. Listar ultimas 100 buscas
  2. Agrupar por: Hoje, Ontem, Ultimos 7 dias, Mais antigas
  3. Exibir: query, modo, fonte, data, resultados
  4. Ordenar por data (mais recente primeiro)

Requisitos Tecnicos:
  Frontend:
    - HistoryTab component
    - Agrupamento por data
    - Cards ou lista
  Storage:
    - LocalStorage + API sync

DoD:
  - [ ] Historico carrega
  - [ ] Agrupamento funciona
  - [ ] Info exibida

Criterios de Aceitacao:
  - [ ] Buscas de hoje agrupadas
  - [ ] Query e modo visiveis
```

---

### CARD HIS-002: Re-executar Busca

```yaml
Titulo: [FRONTEND] Implementar Re-execucao de Busca
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta

Descricao: |
  Re-executar uma busca do historico.

Historia de Usuario: |
  Como recrutador, eu quero re-executar uma busca anterior
  para ver resultados atualizados.

Regras de Negocio:
  1. Botao "Executar" no item do historico
  2. Mesmos parametros (query, modo, fonte, filtros)
  3. Redireciona para tab Busca
  4. Nova entrada no historico

Requisitos Tecnicos:
  Frontend:
    - Botao de play
    - Navigate para tab busca
    - Set parametros

DoD:
  - [ ] Botao funciona
  - [ ] Parametros preservados
  - [ ] Resultados carregam

Criterios de Aceitacao:
  - [ ] Re-executar busca funciona
  - [ ] Modo e fonte preservados
```

---

### CARD HIS-003: Salvar como Favorita

```yaml
Titulo: [FRONTEND] Implementar Salvar Historico como Busca
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media

Descricao: |
  Salvar um item do historico como busca favorita.

Historia de Usuario: |
  Como recrutador, eu quero salvar buscas do historico
  para reutiliza-las facilmente.

Regras de Negocio:
  1. Botao "Salvar" no item
  2. Modal para nome e descricao
  3. Aparece em Buscas Salvas

Requisitos Tecnicos:
  Frontend:
    - Botao Bookmark
    - Modal de salvar
    - Redirect ou toast

DoD:
  - [ ] Modal abre
  - [ ] Busca salva
  - [ ] Aparece em Buscas Salvas

Criterios de Aceitacao:
  - [ ] Salvar com nome funciona
  - [ ] Busca aparece na outra tab
```

---

### CARD HIS-004: Excluir Item

```yaml
Titulo: [FRONTEND] Implementar Exclusao de Item do Historico
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Excluir um item especifico do historico.

Historia de Usuario: |
  Como recrutador, eu quero remover buscas do historico
  que nao preciso mais.

Regras de Negocio:
  1. Botao "Excluir" no item
  2. Sem confirmacao (acao leve)
  3. Item removido
  4. Undo disponivel

Requisitos Tecnicos:
  Frontend:
    - Botao Trash
    - Remocao local
    - Toast com undo

DoD:
  - [ ] Botao funciona
  - [ ] Item removido
  - [ ] Undo funciona

Criterios de Aceitacao:
  - [ ] Excluir item funciona
  - [ ] Undo restaura
```

---

### CARD HIS-005: Limpar Historico

```yaml
Titulo: [FRONTEND] Implementar Limpeza de Historico
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Baixa

Descricao: |
  Limpar todo o historico de buscas.

Historia de Usuario: |
  Como recrutador, eu quero limpar meu historico para
  comecar do zero.

Regras de Negocio:
  1. Botao "Limpar Tudo" no header
  2. Confirmacao obrigatoria
  3. Remove todos os itens
  4. Acao irreversivel

Requisitos Tecnicos:
  Frontend:
    - Botao Limpar
    - AlertDialog
    - Clear all

DoD:
  - [ ] Confirmacao exibida
  - [ ] Historico limpo

Criterios de Aceitacao:
  - [ ] Limpar remove todos os itens
  - [ ] Confirmacao aparece
```

---

### CARD HIS-006: Ver Detalhes

```yaml
Titulo: [FRONTEND] Implementar Detalhes do Historico
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Baixa

Descricao: |
  Ver detalhes completos de um item do historico.

Historia de Usuario: |
  Como recrutador, eu quero ver os detalhes de uma busca
  anterior para entender o que foi buscado.

Regras de Negocio:
  1. Expandir item mostra detalhes
  2. Query completa, modo, fonte
  3. Entidades extraidas
  4. Filtros aplicados

Requisitos Tecnicos:
  Frontend:
    - Accordion ou expand
    - Exibir entidades
    - Exibir filtros

DoD:
  - [ ] Expandir funciona
  - [ ] Detalhes exibidos

Criterios de Aceitacao:
  - [ ] Query completa visivel
  - [ ] Entidades visiveis
```

---

## TAB BUSCAS SALVAS - CARDS JIRA

---

### CARD SAV-001: Listar Buscas Salvas

```yaml
Titulo: [FRONTEND] Implementar Lista de Buscas Salvas
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta

Descricao: |
  Exibir todas as buscas salvas pelo usuario.

Historia de Usuario: |
  Como recrutador, eu quero ver minhas buscas salvas
  para reutiliza-las rapidamente.

Regras de Negocio:
  1. Listar todas as buscas salvas
  2. Card por busca com: nome, query, modo, fonte, stats
  3. Favoritas no topo
  4. Ordenar por ultima utilizacao

Requisitos Tecnicos:
  Frontend:
    - SavedSearchesTab component
    - Grid de cards
  Storage:
    - LocalStorage + API

DoD:
  - [ ] Buscas carregam
  - [ ] Cards exibem info
  - [ ] Favoritas no topo

Criterios de Aceitacao:
  - [ ] Todas as buscas listadas
  - [ ] Stats de uso visiveis
```

---

### CARD SAV-002: Criar Busca

```yaml
Titulo: [FRONTEND] Implementar Criacao de Busca Salva
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta

Descricao: |
  Criar nova busca salva com nome e descricao.

Historia de Usuario: |
  Como recrutador, eu quero salvar buscas para nao precisar
  digita-las novamente.

Regras de Negocio:
  1. Botao "Salvar Busca" na tab Busca
  2. Modal para nome (obrigatorio) e descricao
  3. Salvar query, modo, fonte, filtros
  4. Aparece em Buscas Salvas

Requisitos Tecnicos:
  Frontend:
    - Modal de criacao
    - Form com validacao
  Backend:
    - POST /api/v1/saved-searches

DoD:
  - [ ] Modal funciona
  - [ ] Busca salva
  - [ ] Aparece na lista

Criterios de Aceitacao:
  - [ ] Salvar com nome funciona
  - [ ] Parametros preservados
```

---

### CARD SAV-003: Editar Busca

```yaml
Titulo: [FRONTEND] Implementar Edicao de Busca Salva
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media

Descricao: |
  Editar nome ou descricao de uma busca salva.

Historia de Usuario: |
  Como recrutador, eu quero editar minhas buscas salvas
  para mante-las organizadas.

Regras de Negocio:
  1. Botao "Editar" no card
  2. Modal pre-preenchido
  3. Apenas nome e descricao editaveis
  4. Query nao e editavel

Requisitos Tecnicos:
  Frontend:
    - Modal de edicao
    - Pre-fill
  Backend:
    - PUT /api/v1/saved-searches/{id}

DoD:
  - [ ] Modal funciona
  - [ ] Edicao salva
  - [ ] Query preservada

Criterios de Aceitacao:
  - [ ] Editar nome funciona
  - [ ] Query nao muda
```

---

### CARD SAV-004: Excluir Busca

```yaml
Titulo: [FRONTEND] Implementar Exclusao de Busca Salva
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Excluir uma busca salva.

Historia de Usuario: |
  Como recrutador, eu quero excluir buscas que nao uso mais.

Regras de Negocio:
  1. Botao "Excluir" no menu
  2. Confirmacao opcional
  3. Busca removida
  4. Undo disponivel

Requisitos Tecnicos:
  Frontend:
    - Botao Trash
    - Toast com undo
  Backend:
    - DELETE /api/v1/saved-searches/{id}

DoD:
  - [ ] Exclusao funciona
  - [ ] Undo funciona

Criterios de Aceitacao:
  - [ ] Excluir busca funciona
  - [ ] Undo restaura
```

---

### CARD SAV-005: Executar Busca

```yaml
Titulo: [FRONTEND] Implementar Execucao de Busca Salva
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta

Descricao: |
  Executar uma busca salva.

Historia de Usuario: |
  Como recrutador, eu quero executar buscas salvas com um
  clique para encontrar candidatos rapidamente.

Regras de Negocio:
  1. Botao "Executar" no card
  2. Redireciona para tab Busca
  3. Aplica query, modo, fonte, filtros
  4. Incrementa contador de uso

Requisitos Tecnicos:
  Frontend:
    - Botao Play
    - Navigate com parametros
    - Update stats

DoD:
  - [ ] Executar funciona
  - [ ] Parametros aplicados
  - [ ] Stats atualizadas

Criterios de Aceitacao:
  - [ ] Executar redireciona para busca
  - [ ] Contador incrementa
```

---

### CARD SAV-006: Favoritar Busca

```yaml
Titulo: [FRONTEND] Implementar Favoritar Busca Salva
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Media

Descricao: |
  Marcar busca salva como favorita.

Historia de Usuario: |
  Como recrutador, eu quero favoritar buscas importantes
  para acessa-las mais rapido.

Regras de Negocio:
  1. Icone de estrela no card
  2. Toggle favoritar/desfavoritar
  3. Favoritas aparecem no topo
  4. Ordenacao entre favoritas por uso

Requisitos Tecnicos:
  Frontend:
    - Toggle de estrela
    - Ordenacao local
  Backend:
    - PUT /api/v1/saved-searches/{id} (isFavorite)

DoD:
  - [ ] Toggle funciona
  - [ ] Favoritas no topo

Criterios de Aceitacao:
  - [ ] Favoritar busca funciona
  - [ ] Favoritas aparecem primeiro
```

---

### CARD SAV-007: Ver Estatisticas

```yaml
Titulo: [FRONTEND] Implementar Estatisticas de Busca Salva
Tipo: Feature
Sprint: 3
Pontos: 3
Prioridade: Baixa

Descricao: |
  Exibir estatisticas de uso de uma busca salva.

Historia de Usuario: |
  Como recrutador, eu quero ver quantas vezes usei uma busca
  e a media de resultados.

Regras de Negocio:
  1. Exibir: vezes executada, ultima execucao, media de resultados
  2. Exibir no card ou em expand
  3. Atualizar a cada execucao

Requisitos Tecnicos:
  Frontend:
    - Display de stats no card
    - Formatacao de data
  Storage:
    - usageCount, lastUsed, avgResults

DoD:
  - [ ] Stats exibidas
  - [ ] Atualizadas apos uso

Criterios de Aceitacao:
  - [ ] Contador de uso visivel
  - [ ] Ultima execucao visivel
```

---

### CARD SAV-008: Ordenar Buscas

```yaml
Titulo: [FRONTEND] Implementar Ordenacao de Buscas Salvas
Tipo: Feature
Sprint: 2
Pontos: 2
Prioridade: Baixa

Descricao: |
  Ordenar buscas salvas por diferentes criterios.

Historia de Usuario: |
  Como recrutador, eu quero ordenar minhas buscas por frequencia
  para ver as mais usadas primeiro.

Regras de Negocio:
  1. Ordenar por: Nome, Data criacao, Ultima execucao, Frequencia
  2. Favoritas sempre no topo
  3. Persistir preferencia

Requisitos Tecnicos:
  Frontend:
    - Dropdown de ordenacao
    - LocalStorage

DoD:
  - [ ] Ordenacao funciona
  - [ ] Favoritas no topo
  - [ ] Preferencia persiste

Criterios de Aceitacao:
  - [ ] Ordenar por frequencia funciona
  - [ ] Favoritas permanecem no topo
```

---

## CARDS BACKEND IA - PYTHON/LANGGRAPH (FUN-IA-001 a FUN-IA-008)

> **Especificacao de funcionalidades de IA - JA IMPLEMENTADAS**
> **Total:** 8 cards | **Tecnologia:** Python + FastAPI + LangGraph + Gemini/Claude
> **Stack:** MESMO para prototipo e producao (Python/LangGraph)
> **Status:** Implementado = Pronto para uso em producao
> **Arquivos de Referencia:** lia-agent-system/app/services/

---

### CARD FUN-IA-001: [BACK-IA] WSI Service - Metodologia Cientifica

```yaml
ID: FUN-IA-001
Titulo: [BACK-IA] WSI Service - Metodologia Cientifica de Avaliacao
Tipo: Backend IA
Sprint: 3
Story Points: 13
Prioridade: Critica
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico principal da metodologia WSI (WeDoTalent Skill Index)
  para avaliacao cientifica de candidatos.

Historia de Usuario: |
  Como sistema LIA, eu preciso avaliar candidatos usando
  frameworks cientificos validados.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/wsi_service.py
  Classe: WSIService
  
  Frameworks Implementados:
    1. CBI (Competency-Based Interviewing) - McClelland, 1973
    2. Bloom's Taxonomy (Revisada) - Anderson et al., 2001
    3. Dreyfus Model - Dreyfus & Dreyfus, 1980
    4. Big Five (OCEAN) - Goldberg, 1992
  
  Funcionalidades:
    - Analise de transcricoes de entrevistas
    - Extracao de evidencias comportamentais
    - Calculo de scores tecnicos e comportamentais
    - Determinacao de fit cultural
    - Geracao de parecer automatico

Criterios de Aceitacao:
  - [x] Analise de transcricao funciona
  - [x] Scores calculados corretamente
  - [x] Big Five profile gerado
  - [x] Parecer automatico gerado
```

---

### CARD FUN-IA-002: [BACK-IA] CV Parser Service

```yaml
ID: FUN-IA-002
Titulo: [BACK-IA] CV Parser - Extracao Inteligente de Curriculos
Tipo: Backend IA
Sprint: 2
Story Points: 8
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico para extracao automatica de dados estruturados
  de curriculos usando LLM.

Historia de Usuario: |
  Como recrutador, eu quero que o sistema extraia dados
  do curriculo automaticamente para agilizar o cadastro.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/cv_parser.py
  Classe: CVParserService
  
  Formatos Suportados:
    - PDF
    - DOCX
    - TXT
  
  Dados Extraidos:
    - Nome completo
    - Email e telefone
    - Experiencias profissionais
    - Formacao academica
    - Skills tecnicas
    - Idiomas
    - Certificacoes
  
  Integracao:
    - Claude API para parsing inteligente
    - Prompt template otimizado
    - Fallback para extracao regex

Criterios de Aceitacao:
  - [x] PDF parseado corretamente
  - [x] DOCX parseado corretamente
  - [x] Dados estruturados retornados
  - [x] Skills extraidas como array
```

---

### CARD FUN-IA-003: [BACK-IA] WSI Question Generator

```yaml
ID: FUN-IA-003
Titulo: [BACK-IA] Gerador de Perguntas WSI
Tipo: Backend IA
Sprint: 3
Story Points: 8
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico para geracao automatica de perguntas de triagem
  baseadas em frameworks cientificos.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA sugira perguntas
  relevantes para avaliar competencias especificas.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/wsi_question_generator.py
  Classe: WSIQuestionGenerator
  
  Tipos de Perguntas:
    - CBI (Situacional - STAR)
    - Bloom (Niveis cognitivos)
    - Dreyfus (Nivel de expertise)
    - Big Five (Tracos de personalidade)
  
  Entrada:
    - Job description
    - Competencias requeridas
    - Nivel de senioridade
  
  Saida:
    - Perguntas categorizadas por bloco
    - Criterios de avaliacao
    - Respostas esperadas (ancora)

Criterios de Aceitacao:
  - [x] Perguntas geradas por competencia
  - [x] Categorizacao por framework
  - [x] Criterios de avaliacao inclusos
```

---

### CARD FUN-IA-004: [BACK-IA] Personalized Feedback Service

```yaml
ID: FUN-IA-004
Titulo: [BACK-IA] Feedback Personalizado para Candidatos
Tipo: Backend IA
Sprint: 4
Story Points: 8
Prioridade: Media
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico para geracao de feedback construtivo e personalizado
  para candidatos, incluindo sugestoes de desenvolvimento.

Historia de Usuario: |
  Como recrutador, eu quero enviar feedback personalizado
  para candidatos nao aprovados, de forma automatica.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/personalized_feedback_service.py
  Classe: PersonalizedFeedbackService
  
  Fluxo:
    1. Recruiter solicita feedback de rejeicao
    2. Sistema gera draft personalizado com Claude
    3. Preview para aprovacao/edicao
    4. Envio apos aprovacao
  
  Dados Utilizados:
    - Perfil do candidato
    - Titulo e requisitos da vaga
    - Pontos fortes identificados
    - Areas de desenvolvimento
    - Score WSI e detalhes
  
  Saida:
    - Feedback construtivo
    - Sugestoes de cursos/desenvolvimento
    - Tom profissional e encorajador

Criterios de Aceitacao:
  - [x] Feedback gerado automaticamente
  - [x] Personalizacao baseada no perfil
  - [x] Preview antes de envio
  - [x] Tom construtivo mantido
```

---

### CARD FUN-IA-005: [BACK-IA] Culture Analyzer Service

```yaml
ID: FUN-IA-005
Titulo: [BACK-IA] Analisador de Cultura Empresarial
Tipo: Backend IA
Sprint: 4
Story Points: 8
Prioridade: Media
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico para extracao e analise do perfil cultural de
  empresas a partir de fontes publicas.

Historia de Usuario: |
  Como sistema LIA, eu preciso entender a cultura da empresa
  para avaliar fit cultural dos candidatos.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/culture_analyzer_service.py
  Classe: CultureAnalyzerService
  
  Fontes de Dados:
    - Website da empresa
    - LinkedIn company page
    - Glassdoor (quando disponivel)
    - Job descriptions
  
  Analise:
    - Extracao de valores declarados
    - Mapeamento para tracos Big Five
    - Identificacao de cultura predominante
  
  Saida:
    - Perfil cultural (JSON)
    - Tracos Big Five da empresa
    - Keywords culturais

Criterios de Aceitacao:
  - [x] Extracao de website funciona
  - [x] Big Five mapeado
  - [x] Perfil cultural gerado
```

---

### CARD FUN-IA-006: [BACK-IA] Interview Transcript Analysis

```yaml
ID: FUN-IA-006
Titulo: [BACK-IA] Analise Automatica de Transcricoes de Entrevista
Tipo: Backend IA
Sprint: 5
Story Points: 13
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico para analise automatica de transcricoes de entrevistas
  com scoring WSI determinístico.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA analise a transcricao
  da entrevista e gere scores e insights automaticamente.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/interview_transcript_analysis_service.py
  Classe: InterviewTranscriptAnalysisService
  
  Analises Realizadas:
    - WSI scoring determinístico
    - Bloom Taxonomy (nivel cognitivo)
    - Dreyfus Model (expertise)
    - CBI STAR completeness
    - Big Five profile
  
  Saida:
    - Score por competencia
    - Evidencias extraidas
    - Parecer LIA
    - Sugestao de proxima etapa
  
  Integracoes:
    - Microsoft Teams (transcricao)
    - Notificacoes multi-canal

Criterios de Aceitacao:
  - [x] Transcricao processada
  - [x] WSI scores calculados
  - [x] Big Five gerado
  - [x] Parecer automatico criado
```

---

### CARD FUN-IA-007: [BACK-IA] Semantic Search Service

```yaml
ID: FUN-IA-007
Titulo: [BACK-IA] Busca Semantica de Candidatos
Tipo: Backend IA
Sprint: 2
Story Points: 8
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico de busca semantica usando embeddings e LLM
  para encontrar candidatos por linguagem natural.

Historia de Usuario: |
  Como recrutador, eu quero buscar candidatos usando
  linguagem natural e receber resultados relevantes.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/semantic_search_service.py
  Classe: SemanticSearchService
  
  Tecnologias:
    - Gemini 1.5 Flash para embeddings
    - Redis para cache de resultados
    - PostgreSQL para armazenamento
  
  Funcionalidades:
    - Busca por skills semanticas
    - Busca por experiencia similar
    - Match por descricao de vaga
    - Ranking por relevancia
  
  Cache:
    - Resultados cacheados por 5 minutos
    - Invalidacao por atualizacao de candidato

Criterios de Aceitacao:
  - [x] Busca semantica funciona
  - [x] Cache Redis ativo
  - [x] Ranking por relevancia
```

---

### CARD FUN-IA-008: [BACK-IA] Candidate Enrichment Service

```yaml
ID: FUN-IA-008
Titulo: [BACK-IA] Enriquecimento de Perfil de Candidato
Tipo: Backend IA
Sprint: 4
Story Points: 8
Prioridade: Media
Status: Implementado
Implementado: Janeiro 2026

Descricao: |
  Servico para enriquecimento automatico de perfis de
  candidatos com dados externos e inferencias.

Historia de Usuario: |
  Como recrutador, eu quero ter o perfil do candidato
  enriquecido com informacoes adicionais automaticamente.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/candidate_enrichment_service.py
  Classe: CandidateEnrichmentService
  
  Enriquecimentos:
    - LinkedIn profile data
    - GitHub contributions (devs)
    - Skills inferidas do CV
    - Nivel de senioridade estimado
    - Pretensao salarial estimada
  
  Fontes:
    - APIs publicas
    - Scraping controlado
    - Inferencia por LLM

Criterios de Aceitacao:
  - [x] Enriquecimento funciona
  - [x] Skills inferidas
  - [x] Senioridade estimada
```

---

## RESUMO DE TOTAIS

| Tab | Cards | Total |
|-----|-------|-------|
| Busca | BUS-001 a BUS-027 | 27 |
| Favoritos | FAV-001 a FAV-010 | 10 |
| Listas | LIS-001 a LIS-010 | 10 |
| Historico | HIS-001 a HIS-006 | 6 |
| Buscas Salvas | SAV-001 a SAV-008 | 8 |
| **Backend IA** | FUN-IA-001 a FUN-IA-008 | **8** |
| **TOTAL** | | **69** |

---

## GESTAO DE MUDANCAS E CARDS DE AJUSTE

### Convenção de Nomenclatura

```
CARDS ORIGINAIS:
  FUN-001, KAN-001, ..., FUN-IA-008

CARDS DE AJUSTE (sufixo -A + numero sequencial):
  FUN-001-A1  → Primeiro ajuste do FUN-001
  KAN-003-A1  → Ajuste no Kanban drag-drop
  FUN-IA-001-A1  → Ajuste no WSI Service

TIPOS DE AJUSTE:
  -A  → Ajuste/Alteração (mudança de requisito)
  -B  → Bugfix (correção de bug encontrado)
  -E  → Extensão (nova funcionalidade adicional)
```

### Fluxo de Decisão

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MUDANÇA IDENTIFICADA NA PLATAFORMA                     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  Time já iniciou o card?       │
                    └───────────────┬───────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │ NÃO                 │                     │ SIM
              ▼                     │                     ▼
    ┌─────────────────────┐         │         ┌─────────────────────┐
    │ Atualizar card      │         │         │ Time já finalizou?  │
    │ original diretamente│         │         └──────────┬──────────┘
    │ (incrementar versao)│         │                    │
    └─────────────────────┘         │         ┌──────────┼──────────┐
                                    │         │ NÃO      │          │ SIM
                                    │         ▼          │          ▼
                                    │ ┌───────────────┐  │  ┌───────────────┐
                                    │ │ Criar card    │  │  │ Criar card    │
                                    │ │ XXX-NNN-A1    │  │  │ XXX-NNN-A1    │
                                    │ │ (Ajuste)      │  │  │ (Hotfix)      │
                                    │ └───────────────┘  │  └───────────────┘
                                    │                    │
                                    └────────────────────┘
```

### Template para Card de Ajuste

```yaml
ID: XXX-NNN-A1
Titulo: [AJUSTE] <Titulo do card original> - <Descricao curta da mudanca>
Tipo: Ajuste | Bugfix | Extensao
Sprint: <Sprint atual>
Story Points: <1-5 normalmente>
Prioridade: Alta | Media | Baixa
Card Original: XXX-NNN
Versao Card Original: 1.0
Data Criacao: DD/MM/AAAA
Status Jira: <Backlog | To Do | In Progress | Done>

Motivo da Mudanca: |
  <Explicar por que a mudanca foi necessaria>
  Ex: "Ao testar na plataforma, identificamos que..."

Mudancas Especificas:
  Antes: |
    <Como era antes>
  
  Depois: |
    <Como deve ser agora>

Arquivos Afetados:
  - <caminho/arquivo1.py>
  - <caminho/arquivo2.vue>

Impacto no Desenvolvimento:
  Se ja implementou: |
    <Instrucoes para aplicar o ajuste>
  Se nao implementou: |
    Usar especificacao atualizada do card original

Testes Necessarios:
  - [ ] <Teste 1>
  - [ ] <Teste 2>

Links:
  - Card Original: XXX-NNN
  - Screenshot: <link se houver>
```

### Integracao com Jira

> **API de Sincronizacao disponivel em:** `/api/jira`

**Consultar status de um card:**
```
GET /api/jira?action=issue&key=FUN-001
```

**Consultar multiplos cards:**
```
GET /api/jira?action=issues&keys=FUN-001,KAN-003,FUN-IA-001
```

**Sincronizar com documentacao (detectar divergencias):**
```
POST /api/jira
{
  "action": "sync",
  "issueKeys": ["FUN-001", "KAN-003"],
  "docStatuses": {
    "FUN-001": "Implementado",
    "KAN-003": "Pendente"
  }
}
```

### Registro de Cards de Ajuste

> **Instrução:** Adicionar novos cards de ajuste abaixo conforme forem criados

| ID | Card Original | Tipo | Data | Descrição Resumida | Status |
|----|---------------|------|------|-------------------|--------|
| *Nenhum ajuste registrado ainda* | - | - | - | - | - |

---

## CHANGELOG

| Data | Versao | Alteracao |
|------|--------|-----------|
| Dez/2024 | 1.0 | Criacao inicial - 61 cards |
| 22/01/2026 | 2.0 | Cards IA implementados (FUN-IA-001 a 008), contexto de stack, total 69 cards |
| 22/01/2026 | 2.1 | Secao de Gestao de Mudancas adicionada: convenção de nomenclatura (-A, -B, -E), fluxo de decisão, template para cards de ajuste |
| 22/01/2026 | 2.2 | Integracao com Jira: API de sincronizacao, campo Status Jira nos cards |

---

*Documento gerado para importacao no Jira/Linear/Trello*
