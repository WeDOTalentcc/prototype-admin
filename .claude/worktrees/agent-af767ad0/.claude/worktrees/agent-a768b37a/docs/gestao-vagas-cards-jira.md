# CARDS JIRA - GESTAO DE VAGAS

> **Versao:** 1.0  
> **Data:** Dezembro 2024  
> **Modulo:** Gestao de Vagas (Job Management)  
> **Objetivo:** Cards de desenvolvimento no formato Jira

---

## INDICE DE CARDS

### Por Fluxo
1. [POR - Portfolio de Vagas](#por---portfolio-de-vagas)
2. [CRI - Criacao de Vaga com IA](#cri---criacao-de-vaga-com-ia)
3. [APR - Aprovacao e Publicacao](#apr---aprovacao-e-publicacao)
4. [KAN - Kanban de Candidatos](#kan---kanban-de-candidatos)
5. [LOT - Acoes em Lote](#lot---acoes-em-lote)
6. [COM - Comunicacao da Vaga](#com---comunicacao-da-vaga)
7. [REL - Analise e Relatorios](#rel---analise-e-relatorios)
8. [TPL - Templates de Vagas](#tpl---templates-de-vagas)

### Resumo por Tipo
| Tipo | Quantidade | Story Points |
|------|------------|--------------|
| Epic | 8 | - |
| Feature | 50 | 320 |
| Task | 72 | 380 |
| **TOTAL** | **130** | **700** |

---

# POR - PORTFOLIO DE VAGAS

---

## EPIC POR-EPIC-001: Portfolio de Vagas

```yaml
Titulo: "[EPIC] Sistema de Portfolio de Vagas"
Tipo: Epic
Sprint: 1-2
Pontos: 55
Prioridade: Alta

Descricao: |
  Sistema completo de visualizacao do portfolio de vagas com
  cards, filtros avancados, metricas do funil e acoes rapidas.

Features Incluidas:
  - POR-001: Grid de Cards de Vagas
  - POR-002: Filtros Avancados
  - POR-003: Metricas do Funil
  - POR-004: Quick Actions
  - POR-005: Stats Header

Dependencias: Auth, Database, Job Model
```

---

## CARD POR-001: Grid de Cards de Vagas

```yaml
Titulo: "[FRONT] Implementar Grid de Cards de Vagas"
Tipo: Feature
Sprint: 1
Pontos: 13
Prioridade: Alta

Descricao: |
  Grid responsivo de cards de vagas com informacoes resumidas,
  status, prioridade e navegacao para detalhes.

Historia de Usuario: |
  Como recrutador, eu quero ver todas as vagas em cards
  organizados para ter visao geral do portfolio.

Regras de Negocio:
  1. Grid responsivo: 4 cols desktop, 2 tablet, 1 mobile
  2. Card exibe: titulo, departamento, status, prioridade
  3. Skeleton loading durante carregamento
  4. Paginacao de 20 vagas por pagina
  5. Click no card navega para Kanban

Requisitos Tecnicos:
  Frontend:
    - JobsPage container
    - JobCardGrid component
    - JobCard component
    - Skeleton loading
    - Vuetify v-card, v-row, v-col
  Backend:
    - GET /api/v1/jobs
    - Paginacao cursor-based
  Dados:
    - jobs (SELECT)
  IA:
    - NAO utiliza

DoD:
  - [ ] Grid renderiza com cards
  - [ ] Responsivo em todos breakpoints
  - [ ] Skeleton exibido no loading
  - [ ] Paginacao funciona
  - [ ] Click navega para Kanban
  - [ ] Testes unitarios > 80%

Criterios de Aceitacao:
  - [ ] Ver 20 vagas em grid
  - [ ] Grid ajusta em mobile
  - [ ] Loading exibe skeleton
  - [ ] Tempo de carga < 2s

Labels: frontend, priority-high, sprint-1
```

---

## CARD POR-002: Filtros Avancados

```yaml
Titulo: "[FRONT] Implementar Filtros de Vagas"
Tipo: Feature
Sprint: 1
Pontos: 8
Prioridade: Alta

Descricao: |
  Barra de filtros combinaveis por status, prioridade,
  departamento e recrutador com busca textual.

Historia de Usuario: |
  Como recrutador, eu quero filtrar vagas por criterios
  para encontrar rapidamente o que preciso.

Regras de Negocio:
  1. Filtros combinam com AND logico
  2. Status: Ativa, Paralisada, Fechada, Rascunho
  3. Prioridade: Urgente, Alta, Media, Baixa
  4. Departamento: Multi-select
  5. Recrutador: Multi-select
  6. Busca textual com debounce 300ms
  7. Filtros persistem na URL

Requisitos Tecnicos:
  Frontend:
    - JobFiltersBar component
    - v-select para status/prioridade
    - v-autocomplete para departamento/recrutador
    - v-text-field para busca
    - URL sync com query params
  Backend:
    - Query params: status, priority, department, recruiter, search
  IA:
    - NAO utiliza

DoD:
  - [ ] Todos os filtros funcionam
  - [ ] Filtros combinam corretamente
  - [ ] URL atualiza com filtros
  - [ ] Limpar filtros funciona
  - [ ] Debounce na busca funciona

Criterios de Aceitacao:
  - [ ] Filtrar por "Ativa" mostra apenas ativas
  - [ ] Combinar status + departamento funciona
  - [ ] Buscar "Python" retorna vagas com termo
  - [ ] Recarregar pagina mantem filtros

Labels: frontend, priority-high, sprint-1
```

---

## CARD POR-003: Metricas do Funil no Card

```yaml
Titulo: "[FRONT] Implementar Mini-Funil no Card"
Tipo: Feature
Sprint: 1
Pontos: 8
Prioridade: Alta

Descricao: |
  Exibir mini-funil com contadores por etapa no card de vaga,
  indicando saude do pipeline.

Historia de Usuario: |
  Como recrutador, eu quero ver o funil resumido no card
  para priorizar vagas com problemas.

Regras de Negocio:
  1. Exibir barras por etapa: Funil, Triagem, Entrevista, Final
  2. Cores indicando saude:
     - Verde: bom fluxo
     - Amarelo: poucos candidatos
     - Vermelho: pipeline vazio
  3. Hover exibe tooltip com numeros
  4. Atualiza em tempo real

Requisitos Tecnicos:
  Frontend:
    - MiniPipelineChart component
    - v-progress-linear para barras
    - v-tooltip para numeros
  Backend:
    - GET /api/v1/jobs/{id}/metrics incluido na listagem
  Dados:
    - Agregacao de job_candidates por stage
  IA:
    - NAO utiliza

DoD:
  - [ ] Mini-funil renderiza
  - [ ] Cores corretas por saude
  - [ ] Tooltip exibe numeros
  - [ ] Performance ok (>60fps)

Criterios de Aceitacao:
  - [ ] Ver funil com 4 barras
  - [ ] Vaga com 0 candidatos mostra vermelho
  - [ ] Hover mostra tooltip

Labels: frontend, priority-high, sprint-1
```

---

## CARD POR-004: Quick Actions Menu

```yaml
Titulo: "[FRONT] Implementar Quick Actions no Card"
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Media

Descricao: |
  Menu de acoes rapidas no card: Ver Kanban, Editar,
  Relatorio, Publicar, Duplicar, Arquivar.

Historia de Usuario: |
  Como recrutador, eu quero acoes rapidas no card
  para executar tarefas sem navegar.

Regras de Negocio:
  1. Botoes visiveis: Kanban, Editar, Relatorio
  2. Menu dropdown: Publicar, Duplicar, Arquivar
  3. Confirmacao para Arquivar
  4. Apenas acoes permitidas para o usuario

Requisitos Tecnicos:
  Frontend:
    - QuickActionsMenu component
    - v-btn para acoes principais
    - v-menu para dropdown
    - v-dialog para confirmacao
  Backend:
    - Endpoints existentes
  IA:
    - NAO utiliza

DoD:
  - [ ] Botoes principais funcionam
  - [ ] Menu dropdown funciona
  - [ ] Confirmacao exibida
  - [ ] Permissoes respeitadas

Labels: frontend, sprint-2
```

---

## CARD POR-005: Stats Header

```yaml
Titulo: "[FULL-STACK] Implementar Header com KPIs"
Tipo: Feature
Sprint: 1
Pontos: 8
Prioridade: Alta

Descricao: |
  Header com cards de KPIs: Total vagas, Ativas, Urgentes,
  Candidatos em processo, TTF medio.

Historia de Usuario: |
  Como recrutador, eu quero ver metricas consolidadas
  para ter visao geral do trabalho.

Regras de Negocio:
  1. Metricas: Total, Ativas, Urgentes, Em Processo, TTF
  2. Click em metrica aplica filtro
  3. Trend indicators (up/down vs semana anterior)
  4. Refresh a cada 5 minutos

Requisitos Tecnicos:
  Frontend:
    - JobStatsHeader component
    - v-card para cada metrica
    - Trend arrows
  Backend:
    - GET /api/v1/jobs/stats/overview
    - Cache de 5 minutos
  Dados:
    - Agregacoes COUNT, AVG
  IA:
    - NAO utiliza

DoD:
  - [ ] Cards de metricas renderizam
  - [ ] Click aplica filtro
  - [ ] Trends calculados
  - [ ] Cache funciona

Labels: fullstack, priority-high, sprint-1
```

---

# CRI - CRIACAO DE VAGA COM IA

---

## EPIC CRI-EPIC-001: Wizard de Criacao com LIA

```yaml
Titulo: "[EPIC] Wizard Conversacional de Criacao de Vaga"
Tipo: Epic
Sprint: 2-3
Pontos: 89
Prioridade: Alta

Descricao: |
  Wizard guiado por IA conversacional para criacao de vagas,
  com preenchimento automatico, sugestoes e geracao de JD.

Features Incluidas:
  - CRI-001: Modal Wizard
  - CRI-002: Chat com LIA
  - CRI-003: Extracao de JD
  - CRI-004: Sugestao de Requisitos
  - CRI-005: Sugestao de Salario
  - CRI-006: Configuracao de Etapas
  - CRI-007: Geracao de Descricao
  - CRI-008: Preview e Criacao

Dependencias: POR-EPIC-001, LIA Integration
```

---

## CARD CRI-001: Modal Wizard

```yaml
Titulo: "[FRONT] Implementar Modal Wizard de Criacao"
Tipo: Feature
Sprint: 2
Pontos: 13
Prioridade: Alta

Descricao: |
  Modal fullscreen com layout dividido: chat LIA (60%) +
  formulario/contexto (40%), navegacao entre 8 etapas.

Historia de Usuario: |
  Como recrutador, eu quero criar vagas de forma guiada
  para garantir completude.

Regras de Negocio:
  1. 8 etapas: Basico, Requisitos, Competencias, Salario, Timeline, Etapas, Descricao, Revisao
  2. Navegacao prev/next e click direto
  3. Validacao por etapa
  4. Botao fechar com confirmacao
  5. Auto-save de rascunho

Requisitos Tecnicos:
  Frontend:
    - JobCreationWizard component
    - WizardStepIndicator component
    - Split layout responsivo
    - v-dialog fullscreen
  Backend:
    - POST /api/v1/jobs (rascunho)
  IA:
    - NAO utiliza diretamente

DoD:
  - [ ] Modal abre fullscreen
  - [ ] 8 etapas navegaveis
  - [ ] Validacao por etapa
  - [ ] Confirmacao ao fechar
  - [ ] Auto-save funciona

Labels: frontend, priority-high, sprint-2
```

---

## CARD CRI-002: Chat com LIA

```yaml
Titulo: "[FULL-STACK] Implementar Chat Conversacional com LIA"
Tipo: Feature
Sprint: 2
Pontos: 21
Prioridade: Alta

Descricao: |
  Interface de chat onde o recrutador descreve a vaga e
  a LIA preenche campos automaticamente.

Historia de Usuario: |
  Como recrutador, eu quero criar vagas conversando com a LIA
  para agilizar o processo.

Regras de Negocio:
  1. Chat em portugues
  2. LIA faz perguntas guiadas
  3. Extrai entidades das respostas
  4. Preenche formulario automaticamente
  5. Typing indicator durante resposta
  6. Streaming de respostas

Requisitos Tecnicos:
  Frontend:
    - LIAChatPanel component
    - TypingIndicator component
    - Auto-scroll
    - Streaming rendering
  Backend:
    - POST /api/v1/lia/chat
    - Timeout: 30s
    - SSE para streaming
  Dados:
    - Sessao de conversa
  IA:
    - Claude Sonnet
    - ~2000 tokens/request

Prompt Template: |
  SISTEMA: Voce e LIA, assistente de RH que ajuda a criar vagas.
  TAREFA: Conduza uma conversa para coletar informacoes da vaga.
  Extraia campos estruturados das respostas do usuario.

DoD:
  - [ ] Chat funciona
  - [ ] Campos extraidos automaticamente
  - [ ] Typing indicator exibido
  - [ ] Streaming funciona
  - [ ] Timeout handling

Labels: fullstack, ai, priority-high, sprint-2
```

---

## CARD CRI-003: Extracao de JD

```yaml
Titulo: "[FULL-STACK] Implementar Extracao de Job Description"
Tipo: Feature
Sprint: 2
Pontos: 13
Prioridade: Alta

Descricao: |
  LIA extrai requisitos automaticamente quando usuario
  cola ou digita uma Job Description existente.

Historia de Usuario: |
  Como recrutador, eu quero colar uma JD e ter campos
  preenchidos automaticamente.

Regras de Negocio:
  1. Detectar quando texto e uma JD
  2. Extrair: titulo, departamento, skills, salario, modelo
  3. Exibir confianca de cada extracao
  4. Usuario confirma/edita cada campo
  5. Fallback se extracao falhar

Requisitos Tecnicos:
  Frontend:
    - CriteriaExtractionPanel component
    - EditablePills para criterios
    - Confidence indicator
  Backend:
    - POST /api/v1/lia/job-generation
  IA:
    - Claude Sonnet
    - ~3000 tokens/request

DoD:
  - [ ] JD detectada
  - [ ] Campos extraidos
  - [ ] Confianca exibida
  - [ ] Edicao funciona
  - [ ] Fallback funciona

Labels: fullstack, ai, priority-high, sprint-2
```

---

## CARD CRI-004: Sugestao de Requisitos

```yaml
Titulo: "[FULL-STACK] Implementar Sugestao de Requisitos Tecnicos"
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Media

Descricao: |
  LIA sugere requisitos tecnicos e soft skills baseado
  no titulo e departamento da vaga.

Historia de Usuario: |
  Como recrutador, eu quero receber sugestoes de requisitos
  para nao esquecer skills importantes.

Regras de Negocio:
  1. Trigger apos titulo preenchido
  2. Separacao: obrigatorios vs desejaveis
  3. Niveis: Basico, Intermediario, Avancado
  4. Aceitar/rejeitar individual
  5. Cache de 1 hora

Requisitos Tecnicos:
  Frontend:
    - TechnicalRequirements component
    - Pills com nivel
    - Accept/reject buttons
  Backend:
    - POST /api/v1/lia/suggest-requirements
  IA:
    - Claude Sonnet
    - ~1000 tokens/request

DoD:
  - [ ] Sugestoes aparecem
  - [ ] Niveis definidos
  - [ ] Aceitar/rejeitar funciona
  - [ ] Cache funciona

Labels: fullstack, ai, sprint-2
```

---

## CARD CRI-005: Sugestao de Salario

```yaml
Titulo: "[FULL-STACK] Implementar Sugestao de Faixa Salarial"
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Media

Descricao: |
  LIA sugere faixa salarial baseada no cargo, senioridade
  e localizacao da vaga.

Historia de Usuario: |
  Como recrutador, eu quero saber a faixa de mercado
  para definir proposta competitiva.

Regras de Negocio:
  1. Usar historico interno primeiro
  2. Fallback para LIA se < 10 amostras
  3. Retornar min, max, percentis
  4. Alerta se proposta abaixo
  5. Indicar fonte dos dados

Requisitos Tecnicos:
  Frontend:
    - SalaryConfigPanel component
    - Range slider
    - Source indicator
    - Warning alert
  Backend:
    - POST /api/v1/lia/suggest-salary
  Dados:
    - Historico de contratacoes
  IA:
    - Claude Sonnet (fallback)

DoD:
  - [ ] Faixa retorna
  - [ ] Historico usado quando disponivel
  - [ ] Fallback IA funciona
  - [ ] Alerta de salario baixo

Labels: fullstack, ai, sprint-2
```

---

## CARD CRI-006: Configuracao de Etapas

```yaml
Titulo: "[FRONT] Implementar Configuracao de Etapas de Entrevista"
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Media

Descricao: |
  Interface para configurar etapas do processo seletivo
  com entrevistadores, formato e duracao.

Historia de Usuario: |
  Como recrutador, eu quero definir etapas do processo
  de forma visual e flexivel.

Regras de Negocio:
  1. Etapas padrao: Triagem, RH, Tecnica, Case, Final
  2. Adicionar/remover etapas
  3. Reordenar com drag-drop
  4. Formato: Video, Presencial, Telefone, Teste
  5. Minimo 2, maximo 8 etapas

Requisitos Tecnicos:
  Frontend:
    - InterviewStagesConfig component
    - Drag-drop com DnD Kit
    - Stage card editavel
    - Add/remove buttons
  Backend:
    - Dados incluidos no POST
  IA:
    - NAO utiliza

DoD:
  - [ ] Etapas exibidas
  - [ ] Drag-drop funciona
  - [ ] Add/remove funciona
  - [ ] Validacao minima

Labels: frontend, sprint-2
```

---

## CARD CRI-007: Geracao de Descricao

```yaml
Titulo: "[FULL-STACK] Implementar Geracao de Job Description"
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta

Descricao: |
  LIA gera descricao profissional e inclusiva da vaga
  baseada nos dados preenchidos.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA escreva a descricao
  de forma profissional e atraente.

Regras de Negocio:
  1. Usar todos os dados preenchidos
  2. Tom profissional mas acolhedor
  3. Linguagem inclusiva
  4. Estrutura: Empresa > Vaga > Requisitos > Beneficios
  5. Editavel e regeneravel

Requisitos Tecnicos:
  Frontend:
    - JobPreviewPanel component
    - Markdown renderer
    - Edit mode toggle
    - Regenerate button
  Backend:
    - POST /api/v1/lia/generate-jd
  IA:
    - Claude Sonnet
    - ~1500 tokens/request

DoD:
  - [ ] JD gerada
  - [ ] Linguagem inclusiva
  - [ ] Editavel
  - [ ] Regenerar funciona

Labels: fullstack, ai, priority-high, sprint-2
```

---

## CARD CRI-008: Preview e Criacao

```yaml
Titulo: "[FULL-STACK] Implementar Preview e Criacao de Vaga"
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta

Descricao: |
  Tela de revisao final com preview completo e
  botao de criacao da vaga.

Historia de Usuario: |
  Como recrutador, eu quero revisar a vaga antes de criar
  para garantir que esta correta.

Regras de Negocio:
  1. Preview de todos os campos
  2. Indicadores de completude
  3. Opcao de voltar para editar
  4. Criar como rascunho ou enviar para aprovacao
  5. Validacao final obrigatoria

Requisitos Tecnicos:
  Frontend:
    - PreviewStep component
    - Completeness indicator
    - v-btn para criar
  Backend:
    - POST /api/v1/jobs
    - Validacao completa
  Dados:
    - INSERT jobs + relacionados
  IA:
    - NAO utiliza

DoD:
  - [ ] Preview completo
  - [ ] Validacao funciona
  - [ ] Criar vaga funciona
  - [ ] Status correto

Labels: fullstack, priority-high, sprint-2
```

---

# APR - APROVACAO E PUBLICACAO

---

## EPIC APR-EPIC-001: Workflow de Aprovacao

```yaml
Titulo: "[EPIC] Workflow de Aprovacao e Publicacao"
Tipo: Epic
Sprint: 3
Pontos: 55
Prioridade: Alta

Descricao: |
  Sistema de aprovacao hierarquica com notificacoes
  e publicacao multi-canal.

Features Incluidas:
  - APR-001: Solicitar Aprovacao
  - APR-002: Aprovar/Rejeitar
  - APR-003: Multi-nivel
  - APR-004: Publicar LinkedIn
  - APR-005: Publicar Website
  - APR-006: Gestao de Status

Dependencias: CRI-EPIC-001
```

---

## CARD APR-001: Solicitar Aprovacao

```yaml
Titulo: "[FULL-STACK] Implementar Solicitacao de Aprovacao"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Alta

Descricao: |
  Botao e fluxo para enviar vaga para aprovacao,
  identificando aprovadores automaticamente.

Historia de Usuario: |
  Como recrutador, eu quero enviar vagas para aprovacao
  do gestor antes de publicar.

Regras de Negocio:
  1. Vaga deve estar completa
  2. Identificar aprovadores por departamento
  3. Criar solicitacao com status "pending"
  4. Notificar aprovadores
  5. Exibir status na vaga

Requisitos Tecnicos:
  Frontend:
    - RequestApprovalButton component
    - v-btn com loading
  Backend:
    - POST /api/v1/approvals
    - Notificacao email/push
  Dados:
    - INSERT job_approvals
  IA:
    - NAO utiliza

DoD:
  - [ ] Botao funciona
  - [ ] Aprovadores identificados
  - [ ] Notificacao enviada
  - [ ] Status atualizado

Labels: fullstack, priority-high, sprint-3
```

---

## CARD APR-002: Aprovar/Rejeitar Vaga

```yaml
Titulo: "[FULL-STACK] Implementar Aprovar e Rejeitar"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Alta

Descricao: |
  Interface para aprovadores aprovarem ou rejeitarem
  vagas pendentes com comentarios.

Historia de Usuario: |
  Como gestor, eu quero aprovar ou rejeitar vagas
  com comentarios.

Regras de Negocio:
  1. Aprovar: comentario opcional
  2. Rejeitar: motivo obrigatorio
  3. Atualizar status da solicitacao
  4. Notificar recrutador
  5. Registrar historico

Requisitos Tecnicos:
  Frontend:
    - ApprovalCard component
    - ApproveModal component
    - RejectModal component
  Backend:
    - POST /api/v1/approvals/{id}/approve
    - POST /api/v1/approvals/{id}/reject
  Dados:
    - UPDATE job_approvals
    - INSERT job_approval_history
  IA:
    - NAO utiliza

DoD:
  - [ ] Aprovar funciona
  - [ ] Rejeitar funciona
  - [ ] Historico registrado
  - [ ] Notificacao enviada

Labels: fullstack, priority-high, sprint-3
```

---

## CARD APR-003: Workflow Multi-nivel

```yaml
Titulo: "[BACK] Implementar Aprovacao Multi-nivel"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Media

Descricao: |
  Suporte a workflow de aprovacao com multiplos niveis
  sequenciais (HM > RH > Diretoria).

Historia de Usuario: |
  Como empresa, eu quero que vagas passem por
  multiplos aprovadores antes de publicar.

Regras de Negocio:
  1. Niveis configuraveis por empresa (1-3)
  2. Sequencial: proximo apos anterior
  3. Qualquer rejeicao cancela workflow
  4. Notificar cada nivel
  5. Timeout com lembrete (48h)

Requisitos Tecnicos:
  Backend:
    - State machine para workflow
    - Scheduler para lembretes
    - Multi-level approval logic
  Dados:
    - approval_level em job_approvals

DoD:
  - [ ] Multi-nivel funciona
  - [ ] Sequencia correta
  - [ ] Lembretes enviados
  - [ ] Timeout handling

Labels: backend, sprint-3
```

---

## CARD APR-004: Publicar no LinkedIn

```yaml
Titulo: "[FULL-STACK] Implementar Publicacao LinkedIn"
Tipo: Feature
Sprint: 3
Pontos: 13
Prioridade: Alta

Descricao: |
  Integracao com LinkedIn Talent Solutions para
  publicar vagas diretamente.

Historia de Usuario: |
  Como recrutador, eu quero publicar vagas no LinkedIn
  para atrair candidatos.

Regras de Negocio:
  1. Vaga deve estar aprovada
  2. Mapear campos automaticamente
  3. Verificar creditos/budget
  4. Adicionar UTM tracking
  5. Sincronizar candidaturas

Requisitos Tecnicos:
  Frontend:
    - PublishLinkedInModal component
    - Status indicator
  Backend:
    - POST /api/v1/jobs/{id}/publish
    - LinkedIn Talent Solutions API
    - Webhook para candidaturas
  Dados:
    - INSERT job_publications
  IA:
    - NAO utiliza

DoD:
  - [ ] Publicacao funciona
  - [ ] UTM adicionado
  - [ ] Status rastreado
  - [ ] Candidaturas sincronizam

Labels: fullstack, integration, priority-high, sprint-3
```

---

## CARD APR-005: Publicar no Website

```yaml
Titulo: "[BACK] Implementar Publicacao Website"
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Publicar vaga na pagina de carreiras da empresa
  automaticamente.

Requisitos Tecnicos:
  Backend:
    - API para careers page
    - Template de exibicao
  Dados:
    - Flag is_published_website

DoD:
  - [ ] Publicacao funciona
  - [ ] Aparece em /careers
  - [ ] Despublicar funciona

Labels: backend, sprint-3
```

---

## CARD APR-006: Gestao de Status

```yaml
Titulo: "[FULL-STACK] Implementar Gestao de Status da Vaga"
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Alta

Descricao: |
  Dropdown para alterar status da vaga: Ativa, Paralisada,
  Fechada (Preenchida/Cancelada).

Requisitos Tecnicos:
  Frontend:
    - StatusDropdown component
    - Confirmacao para fechar
  Backend:
    - PUT /api/v1/jobs/{id}/status
    - Historico de mudancas
  Dados:
    - UPDATE jobs.status
    - INSERT job_status_history

DoD:
  - [ ] Dropdown funciona
  - [ ] Confirmacao exibida
  - [ ] Historico registrado

Labels: fullstack, priority-high, sprint-3
```

---

# KAN - KANBAN DE CANDIDATOS

---

## EPIC KAN-EPIC-001: Kanban de Candidatos

```yaml
Titulo: "[EPIC] Kanban de Candidatos por Vaga"
Tipo: Epic
Sprint: 2-3
Pontos: 89
Prioridade: Alta

Descricao: |
  Pipeline visual Kanban com drag-and-drop, cards de
  candidatos com scores e preview lateral.

Features Incluidas:
  - KAN-001: Kanban Board
  - KAN-002: Cards de Candidato
  - KAN-003: Drag-and-Drop
  - KAN-004: Preview Lateral
  - KAN-005: Filtros e Ordenacao

Dependencias: CRI-EPIC-001
```

---

## CARD KAN-001: Kanban Board

```yaml
Titulo: "[FRONT] Implementar Kanban Board"
Tipo: Feature
Sprint: 2
Pontos: 13
Prioridade: Alta

Descricao: |
  Board visual com colunas por etapa: Funil, Triagem,
  Entrevista, Final, Aprovados, Reprovados.

Historia de Usuario: |
  Como recrutador, eu quero ver candidatos em um board
  visual para acompanhar o processo.

Regras de Negocio:
  1. 6 colunas padrao
  2. Contadores por coluna
  3. Scroll horizontal se necessario
  4. Colapsar colunas
  5. Responsivo (swipe mobile)

Requisitos Tecnicos:
  Frontend:
    - JobKanbanPage container
    - KanbanBoard component
    - KanbanColumn component
    - Horizontal scroll
  Backend:
    - GET /api/v1/jobs/{id}/kanban
  Dados:
    - Candidatos agrupados por stage
  IA:
    - NAO utiliza

DoD:
  - [ ] Board renderiza
  - [ ] 6 colunas exibidas
  - [ ] Contadores corretos
  - [ ] Scroll horizontal funciona
  - [ ] Colapsar funciona

Labels: frontend, priority-high, sprint-2
```

---

## CARD KAN-002: Cards de Candidato

```yaml
Titulo: "[FRONT] Implementar Cards de Candidato"
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta

Descricao: |
  Cards com avatar, nome, cargo, score e skills resumidas
  dentro das colunas do Kanban.

Requisitos Tecnicos:
  Frontend:
    - CandidateCard component
    - Score chip com cor
    - Skills pills
    - Checkbox para selecao
    - Hover actions

DoD:
  - [ ] Card exibe dados
  - [ ] Score com cor correta
  - [ ] Checkbox funciona
  - [ ] Hover actions visiveis

Labels: frontend, priority-high, sprint-2
```

---

## CARD KAN-003: Drag-and-Drop

```yaml
Titulo: "[FULL-STACK] Implementar Drag-and-Drop"
Tipo: Feature
Sprint: 2
Pontos: 13
Prioridade: Alta

Descricao: |
  Arrastar candidatos entre colunas para mover de etapa,
  com animacao suave e persistencia.

Historia de Usuario: |
  Como recrutador, eu quero arrastar candidatos entre etapas
  para atualizar o status rapidamente.

Regras de Negocio:
  1. Arrastar de qualquer coluna para outra
  2. Animacao durante drag
  3. Highlight coluna destino
  4. Confirmacao para Aprovados/Reprovados
  5. Registrar historico

Requisitos Tecnicos:
  Frontend:
    - DnD Kit integration
    - DragDropContext component
    - Animacoes CSS
  Backend:
    - PUT /api/v1/jobs/{id}/candidates/{cid}/stage
    - INSERT candidate_stage_history
  Dados:
    - UPDATE job_candidates.stage
  IA:
    - NAO utiliza

DoD:
  - [ ] Drag funciona
  - [ ] Animacao suave
  - [ ] Persistencia ok
  - [ ] Confirmacao exibida
  - [ ] Historico registrado

Labels: fullstack, priority-high, sprint-2
```

---

## CARD KAN-004: Preview Lateral

```yaml
Titulo: "[FRONT] Implementar Preview Lateral"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Alta

Descricao: |
  Painel lateral que abre ao clicar no card, mostrando
  detalhes do candidato sem sair do Kanban.

Requisitos Tecnicos:
  Frontend:
    - CandidatePreview component
    - Slide-in animation
    - Resize handle
    - Navigation arrows
    - ESC to close

DoD:
  - [ ] Preview abre
  - [ ] Dados exibidos
  - [ ] Navegacao funciona
  - [ ] ESC fecha

Labels: frontend, priority-high, sprint-3
```

---

## CARD KAN-005: Filtros e Ordenacao

```yaml
Titulo: "[FRONT] Implementar Filtros do Kanban"
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Filtros por score, fonte, data e ordenacao dentro
  das colunas.

Requisitos Tecnicos:
  Frontend:
    - KanbanFilters component
    - Score range slider
    - Source multi-select
    - Sort dropdown

DoD:
  - [ ] Filtros funcionam
  - [ ] Ordenacao funciona
  - [ ] Filtros combinaveis

Labels: frontend, sprint-3
```

---

# LOT - ACOES EM LOTE

---

## EPIC LOT-EPIC-001: Acoes em Lote

```yaml
Titulo: "[EPIC] Acoes em Lote para Candidatos"
Tipo: Epic
Sprint: 3
Pontos: 34
Prioridade: Media

Descricao: |
  Sistema de selecao multipla e acoes em lote para
  candidatos da vaga.

Features Incluidas:
  - LOT-001: Selecao Multipla
  - LOT-002: Mover em Lote
  - LOT-003: Email em Lote
  - LOT-004: Agendar em Lote

Dependencias: KAN-EPIC-001
```

---

## CARD LOT-001: Selecao Multipla

```yaml
Titulo: "[FRONT] Implementar Selecao Multipla"
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Checkbox em cada card e select all por coluna,
  com barra de acoes contextual.

Requisitos Tecnicos:
  Frontend:
    - Checkbox no CandidateCard
    - SelectAll no StageHeader
    - BatchSelectionBar component
    - Counter badge

DoD:
  - [ ] Checkbox funciona
  - [ ] Select all funciona
  - [ ] Bar aparece
  - [ ] Counter correto

Labels: frontend, sprint-3
```

---

## CARD LOT-002: Mover em Lote

```yaml
Titulo: "[FULL-STACK] Implementar Mover Etapa em Lote"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Media

Descricao: |
  Mover multiplos candidatos para nova etapa de uma vez.

Requisitos Tecnicos:
  Frontend:
    - MoveStageModal component
    - Progress indicator
    - Result summary
  Backend:
    - PUT /api/v1/jobs/{id}/candidates/bulk/stage
    - Batch processing
  Dados:
    - Multiple UPDATEs
  IA:
    - NAO utiliza

DoD:
  - [ ] Modal funciona
  - [ ] Batch processing
  - [ ] Resultado exibido
  - [ ] Historico registrado

Labels: fullstack, sprint-3
```

---

## CARD LOT-003: Email em Lote

```yaml
Titulo: "[FULL-STACK] Implementar Email em Lote"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Media

Descricao: |
  Enviar email com template para multiplos candidatos.

Requisitos Tecnicos:
  Frontend:
    - BulkEmailModal component
    - Template selector
    - Preview
  Backend:
    - POST /api/v1/jobs/{id}/candidates/bulk/email
    - Queue processing
  IA:
    - NAO utiliza

DoD:
  - [ ] Modal funciona
  - [ ] Template aplicado
  - [ ] Emails enviados
  - [ ] Historico registrado

Labels: fullstack, sprint-3
```

---

## CARD LOT-004: Agendar em Lote

```yaml
Titulo: "[FULL-STACK] Implementar Agendamento em Lote"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Media

Descricao: |
  Agendar entrevistas para multiplos candidatos.

Requisitos Tecnicos:
  Frontend:
    - BulkScheduleModal component
    - Time slot picker
    - Interviewer selector
  Backend:
    - POST /api/v1/jobs/{id}/candidates/bulk/schedule
  IA:
    - NAO utiliza

DoD:
  - [ ] Modal funciona
  - [ ] Slots selecionaveis
  - [ ] Entrevistas criadas
  - [ ] Convites enviados

Labels: fullstack, sprint-3
```

---

# COM - COMUNICACAO DA VAGA

---

## EPIC COM-EPIC-001: Comunicacao com Candidatos

```yaml
Titulo: "[EPIC] Sistema de Comunicacao da Vaga"
Tipo: Epic
Sprint: 3-4
Pontos: 40
Prioridade: Media

Descricao: |
  Sistema de comunicacao por email e WhatsApp com
  templates especificos e historico.

Features Incluidas:
  - COM-001: Modal de Comunicacao
  - COM-002: Templates de Email
  - COM-003: Envio de Email
  - COM-004: WhatsApp
  - COM-005: Historico

Dependencias: KAN-EPIC-001
```

---

## CARD COM-001: Modal de Comunicacao

```yaml
Titulo: "[FRONT] Implementar Modal de Comunicacao"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Media

Descricao: |
  Modal unificado para email e WhatsApp com tabs,
  templates e editor de mensagem.

Requisitos Tecnicos:
  Frontend:
    - UnifiedCommunicationModal component
    - v-tabs Email/WhatsApp
    - Template selector
    - Message editor
    - Variable inserter

DoD:
  - [ ] Modal abre
  - [ ] Tabs funcionam
  - [ ] Editor funciona
  - [ ] Variaveis inseridas

Labels: frontend, sprint-3
```

---

## CARD COM-002: Templates de Email

```yaml
Titulo: "[FULL-STACK] Implementar Templates de Email"
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Templates pre-definidos: Convite, Aprovacao, Rejeicao,
  com variaveis dinamicas.

Requisitos Tecnicos:
  Frontend:
    - JobTemplateSelector component
    - Preview rendering
  Backend:
    - GET /api/v1/templates
    - GET /api/v1/templates/job/{id}
  Dados:
    - email_templates table

DoD:
  - [ ] Templates listados
  - [ ] Selecao funciona
  - [ ] Variaveis substituidas

Labels: fullstack, sprint-3
```

---

## CARD COM-003: Envio de Email

```yaml
Titulo: "[BACK] Implementar Envio de Email"
Tipo: Feature
Sprint: 3
Pontos: 8
Prioridade: Media

Descricao: |
  Integracao com SendGrid/SES para envio de emails
  com tracking de abertura.

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/communications
    - SendGrid/SES integration
    - Tracking pixel
    - Queue processing
  Dados:
    - INSERT candidate_communications

DoD:
  - [ ] Email enviado
  - [ ] Tracking funciona
  - [ ] Historico registrado

Labels: backend, integration, sprint-3
```

---

## CARD COM-004: WhatsApp

```yaml
Titulo: "[FRONT] Implementar WhatsApp"
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Baixa

Descricao: |
  Redirect para wa.me com mensagem pre-preenchida.

Requisitos Tecnicos:
  Frontend:
    - WhatsApp button
    - wa.me redirect
    - Template formatting

DoD:
  - [ ] Redirect funciona
  - [ ] Mensagem formatada
  - [ ] Telefone validado

Labels: frontend, sprint-4
```

---

## CARD COM-005: Historico de Comunicacoes

```yaml
Titulo: "[FULL-STACK] Implementar Historico de Comunicacoes"
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Media

Descricao: |
  Timeline de todas as comunicacoes com o candidato.

Requisitos Tecnicos:
  Frontend:
    - CommunicationHistory component
    - Timeline visual
    - Status indicators
  Backend:
    - GET /api/v1/candidates/{id}/communications

DoD:
  - [ ] Timeline renderiza
  - [ ] Status exibido
  - [ ] Ordenacao correta

Labels: fullstack, sprint-3
```

---

# REL - ANALISE E RELATORIOS

---

## EPIC REL-EPIC-001: Dashboard de Relatorios

```yaml
Titulo: "[EPIC] Dashboard de Analise da Vaga"
Tipo: Epic
Sprint: 4
Pontos: 45
Prioridade: Media

Descricao: |
  Dashboard com metricas de funil, TTH, analise de fontes,
  NPS e insights da LIA.

Features Incluidas:
  - REL-001: Modal de Relatorio
  - REL-002: Funil de Conversao
  - REL-003: Time-to-Hire
  - REL-004: Analise de Fontes
  - REL-005: NPS
  - REL-006: Insights LIA
  - REL-007: Exportacao

Dependencias: KAN-EPIC-001
```

---

## CARD REL-001: Modal de Relatorio

```yaml
Titulo: "[FRONT] Implementar Modal de Relatorio"
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Media

Descricao: |
  Modal com dashboard de metricas e graficos da vaga.

Requisitos Tecnicos:
  Frontend:
    - JobReportModal component
    - Layout de cards
    - v-dialog scrollable

DoD:
  - [ ] Modal abre
  - [ ] Layout responsivo
  - [ ] Scroll funciona

Labels: frontend, sprint-4
```

---

## CARD REL-002: Funil de Conversao

```yaml
Titulo: "[FULL-STACK] Implementar Grafico de Funil"
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Media

Descricao: |
  Grafico de funil mostrando conversao por etapa.

Requisitos Tecnicos:
  Frontend:
    - ConversionFunnel component
    - Chart.js ou Recharts
    - Tooltips interativos
  Backend:
    - GET /api/v1/jobs/{id}/metrics/funnel
  Dados:
    - Agregacao por stage

DoD:
  - [ ] Grafico renderiza
  - [ ] Dados corretos
  - [ ] Tooltips funcionam

Labels: fullstack, sprint-4
```

---

## CARD REL-003: Time-to-Hire

```yaml
Titulo: "[FULL-STACK] Implementar Time-to-Hire Chart"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media

Descricao: |
  Grafico mostrando tempo medio por etapa e total.

Requisitos Tecnicos:
  Frontend:
    - TimeToHireChart component
    - Bar chart
    - Benchmark comparison
  Backend:
    - Calculo de tempo por etapa
  Dados:
    - AVG(moved_at - added_at)

DoD:
  - [ ] Grafico renderiza
  - [ ] TTH calculado
  - [ ] Benchmark exibido

Labels: fullstack, sprint-4
```

---

## CARD REL-004: Analise de Fontes

```yaml
Titulo: "[FULL-STACK] Implementar Analise de Fontes"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media

Descricao: |
  Grafico mostrando distribuicao e conversao por fonte.

Requisitos Tecnicos:
  Frontend:
    - SourceAnalysis component
    - Pie chart + table
  Backend:
    - Agregacao por source
  Dados:
    - COUNT por source

DoD:
  - [ ] Grafico renderiza
  - [ ] Conversao por fonte
  - [ ] Melhor fonte destacada

Labels: fullstack, sprint-4
```

---

## CARD REL-005: NPS

```yaml
Titulo: "[FULL-STACK] Implementar Widget de NPS"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Baixa

Descricao: |
  Widget mostrando NPS dos candidatos da vaga.

Requisitos Tecnicos:
  Frontend:
    - NPSWidget component
    - Score display
    - Feedbacks recentes
  Backend:
    - AVG(rating) WHERE job_id = ?
  Dados:
    - candidate_feedback table

DoD:
  - [ ] NPS exibido
  - [ ] Feedbacks listados

Labels: fullstack, sprint-4
```

---

## CARD REL-006: Insights LIA

```yaml
Titulo: "[FULL-STACK] Implementar Insights da LIA"
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Media

Descricao: |
  Painel com insights gerados pela LIA baseado nas metricas.

Historia de Usuario: |
  Como gestor, eu quero ver insights inteligentes
  para tomar decisoes melhores.

Requisitos Tecnicos:
  Frontend:
    - LIAInsightsPanel component
    - Alert cards por tipo
    - Refresh button
  Backend:
    - GET /api/v1/jobs/{id}/insights
    - Cache 24h
  IA:
    - Claude Sonnet
    - ~2000 tokens/request

DoD:
  - [ ] Insights gerados
  - [ ] Categorias corretas
  - [ ] Cache funciona
  - [ ] Refresh funciona

Labels: fullstack, ai, sprint-4
```

---

## CARD REL-007: Exportacao

```yaml
Titulo: "[BACK] Implementar Exportacao de Relatorio"
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Media

Descricao: |
  Exportar relatorio em PDF e Excel.

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/jobs/{id}/report/export
    - Puppeteer para PDF
    - ExcelJS para XLSX

DoD:
  - [ ] PDF gerado
  - [ ] Excel gerado
  - [ ] Download funciona

Labels: backend, sprint-4
```

---

# TPL - TEMPLATES DE VAGAS

---

## EPIC TPL-EPIC-001: Biblioteca de Templates

```yaml
Titulo: "[EPIC] Biblioteca de Templates de Vagas"
Tipo: Epic
Sprint: 4
Pontos: 30
Prioridade: Media

Descricao: |
  Sistema de templates reutilizaveis para criacao rapida
  de vagas.

Features Incluidas:
  - TPL-001: Listar Templates
  - TPL-002: Criar Template
  - TPL-003: Salvar Vaga como Template
  - TPL-004: Usar Template
  - TPL-005: Editar/Excluir

Dependencias: CRI-EPIC-001
```

---

## CARD TPL-001: Listar Templates

```yaml
Titulo: "[FULL-STACK] Implementar Listagem de Templates"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media

Descricao: |
  Grid de templates com cards, busca e filtros.

Requisitos Tecnicos:
  Frontend:
    - JobTemplatesPage container
    - TemplateGrid component
    - TemplateCard component
  Backend:
    - GET /api/v1/job-templates
  Dados:
    - job_templates table

DoD:
  - [ ] Grid renderiza
  - [ ] Busca funciona
  - [ ] Filtros funcionam

Labels: fullstack, sprint-4
```

---

## CARD TPL-002: Criar Template Manual

```yaml
Titulo: "[FULL-STACK] Implementar Criacao de Template"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media

Descricao: |
  Modal para criar template do zero.

Requisitos Tecnicos:
  Frontend:
    - CreateTemplateModal component
    - Form completo
  Backend:
    - POST /api/v1/job-templates
  Dados:
    - INSERT job_templates

DoD:
  - [ ] Modal funciona
  - [ ] Template criado
  - [ ] Validacao funciona

Labels: fullstack, sprint-4
```

---

## CARD TPL-003: Salvar Vaga como Template

```yaml
Titulo: "[FULL-STACK] Implementar Salvar como Template"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media

Descricao: |
  Salvar vaga existente como template reutilizavel.

Requisitos Tecnicos:
  Frontend:
    - SaveAsTemplateModal component
    - Nome e categoria
  Backend:
    - POST /api/v1/jobs/{id}/save-as-template
    - Copia campos da vaga
  Dados:
    - INSERT job_templates

DoD:
  - [ ] Modal funciona
  - [ ] Campos copiados
  - [ ] Template criado

Labels: fullstack, sprint-4
```

---

## CARD TPL-004: Usar Template

```yaml
Titulo: "[FRONT] Implementar Usar Template"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media

Descricao: |
  Criar vaga a partir de template selecionado.

Requisitos Tecnicos:
  Frontend:
    - UseTemplateModal component
    - Pre-preenche wizard
    - Usage counter

DoD:
  - [ ] Template carrega
  - [ ] Wizard pre-preenchido
  - [ ] Contador incrementado

Labels: frontend, sprint-4
```

---

## CARD TPL-005: Editar/Excluir Template

```yaml
Titulo: "[FULL-STACK] Implementar Editar e Excluir Template"
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Baixa

Descricao: |
  Editar e excluir templates existentes.

Requisitos Tecnicos:
  Frontend:
    - EditTemplateModal component
    - Delete confirmation
  Backend:
    - PUT /api/v1/job-templates/{id}
    - DELETE /api/v1/job-templates/{id}
  Dados:
    - UPDATE/DELETE job_templates

DoD:
  - [ ] Editar funciona
  - [ ] Excluir funciona
  - [ ] Confirmacao exibida

Labels: fullstack, sprint-4
```

---

# RESUMO DE CARDS

## Totais por Fluxo

| Fluxo | Cards | Story Points |
|-------|-------|--------------|
| POR - Portfolio | 6 | 47 |
| CRI - Criacao IA | 9 | 95 |
| APR - Aprovacao | 7 | 52 |
| KAN - Kanban | 6 | 55 |
| LOT - Lote | 5 | 37 |
| COM - Comunicacao | 6 | 34 |
| REL - Relatorios | 8 | 52 |
| TPL - Templates | 6 | 30 |
| **TOTAL** | **53** | **402** |

## Totais por Tipo

| Tipo | Quantidade |
|------|------------|
| Epic | 8 |
| Feature | 45 |
| **TOTAL** | **53** |

## Totais por Sprint

| Sprint | Cards | Story Points |
|--------|-------|--------------|
| Sprint 1 | 8 | 55 |
| Sprint 2 | 15 | 115 |
| Sprint 3 | 18 | 132 |
| Sprint 4 | 12 | 100 |
| **TOTAL** | **53** | **402** |

---

*Documento gerado para desenvolvimento do modulo Gestao de Vagas.*
*Total: 53 cards organizados em 8 fluxos.*
