# PLATAFORMA LIA MVP — CARDS JIRA v2: GESTÃO DE VAGAS E CONFIGURAÇÃO DE TRIAGEM

**Data:** Fevereiro 2026  
**Versão:** 1.0  
**Última Atualização:** 16 Fevereiro 2026 (v1.1 — Modelo Unificado de Benefícios)  
**Status:** 📋 Documento de Avaliação — Pendente revisão antes de merge no lia-mvp-cards-jira.md principal

---

## INFORMAÇÕES DO ÉPICO

| Campo | Valor |
|-------|-------|
| **Épico** | É5 — Gestão de Vagas e Configuração de Triagem |
| **Código** | EPIC-CFG |
| **Sprint** | A definir |
| **Início** | A definir |
| **Término** | A definir |
| **Status** | 📋 Pendente Jira |

---

## RESUMO QUANTITATIVO

| Indicador | Quantidade |
|-----------|------------|
| **Total de Cards** | 12 |
| **Frontend** | 2 (CFG-001, CFG-011) |
| **Full-Stack** | 10 (CFG-002, CFG-003, CFG-004, CFG-005, CFG-006, CFG-007, CFG-008, CFG-009, CFG-010, CFG-012) |
| **Backend** | 0 |
| **IA** | 0 (componentes de IA integrados dentro dos cards Full-Stack: geração WSI, avaliação JD, sugestões de competências) |
| **Total de Pontos** | 68 |
| **Prioridade Crítica** | 6 (CFG-001, CFG-002, CFG-003, CFG-005, CFG-007, CFG-012) |
| **Prioridade Alta** | 4 (CFG-006, CFG-008, CFG-009, CFG-011) |
| **Prioridade Média** | 2 (CFG-004, CFG-010) |

---

## TABELA RESUMO DOS CARDS

| Card | Título | Área | Pontos | Prioridade | Dependências |
|------|--------|------|--------|------------|--------------|
| CFG-001 | Preview da Vaga (Painel Lateral) | Frontend | 5 | Crítica | — |
| CFG-002 | Tab Configurações da Vaga — Informações Gerais | Full-Stack | 8 | Crítica | CFG-001 |
| CFG-003 | Tab Configurações da Vaga — Processo Seletivo | Full-Stack | 5 | Crítica | CFG-002, CFG-008 |
| CFG-004 | Tab Configurações da Vaga — Pessoas e Remuneração | Full-Stack | 3 | Média | CFG-002 |
| CFG-005 | Tab Configurações da Vaga — Configurações do Roteiro de Triagem | Full-Stack | 5 | Crítica | CFG-002 |
| CFG-006 | Tab Configurações da Vaga — Descrição do Cargo para Triagem | Full-Stack | 5 | Alta | CFG-005 |
| CFG-007 | Tab Configurações da Vaga — Perguntas de Triagem (Blocos WSI) | Full-Stack | 8 | Crítica | CFG-005, CFG-006, CFG-009 |
| CFG-008 | Menu Configurações — Pipeline de Recrutamento | Full-Stack | 5 | Alta | — |
| CFG-009 | Menu Configurações — Perguntas de Elegibilidade (Banco Central) | Full-Stack | 8 | Alta | — |
| CFG-010 | Menu Configurações — Status de Candidatos, Solicitação de Dados e Instruções LIA | Full-Stack | 5 | Média | — |
| CFG-011 | Coluna Status de Triagem na Tabela de Vagas | Frontend | 3 | Alta | CFG-005 |
| CFG-012 | Integrações e Vinculações entre Componentes | Full-Stack | 8 | Crítica | CFG-001 a CFG-011 |

---

## CARDS DETALHADOS

---

### CFG-001: Preview da Vaga (Painel Lateral)

```yaml
Titulo: "[FRONTEND] Preview da Vaga — Painel Lateral"
Tipo: Feature
Area: Frontend
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 5
Prioridade: Crítica
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: Nenhuma

Descricao: |
  Painel lateral de preview que aparece ao lado da tabela de vagas quando uma vaga é selecionada.
  Exibe um resumo completo e read-only da vaga em seções organizadas verticalmente.
  Inclui botão para expandir/abrir a visualização completa da vaga.
  REMOVIDO: botão para editar/criar roteiro de triagem a partir do preview.

  Seções na ordem:
  1. Descrição da Vaga — com "Ver mais"/"Ver menos" para textos > 300 caracteres
  2. Competências Técnicas — badges cinza
  3. Competências Comportamentais — badges roxos
  4. Idiomas — com nível e badge "Obrigatório"
  5. Remuneração e Benefícios — faixa salarial formatada como R$, faixa de bônus, BenefitBadgeList com ícones por categoria (8 categorias), tooltips com valor/carência/obrigatoriedade, BenefitDetailsSheet para "+N mais"
  6. Etapas do Processo — pipeline horizontal com chevrons, indicador LIA-assisted (ponto cyan)
  7. Ações Afirmativas — condicional, fundo roxo, mostra tipo e critério
  8. Fluxo de Triagem WSI — contagem de perguntas, tempo estimado, badge de status Ativo/Pausado
  9. Agendamento — score mínimo, calendário, horários, duração
  10. Canais de Comunicação — badges de canal, score mínimo aprovação, timeout, re-tentativas, fallback

Historia de Usuario: |
  Como recrutador, eu quero visualizar um resumo completo da vaga em um painel lateral
  para avaliar rapidamente as configurações sem precisar abrir a tela de edição.

Regras de Negocio:
  1. Descrições com mais de 300 caracteres devem ser truncadas com botão "Ver mais"/"Ver menos"
  2. Seção de Ações Afirmativas só aparece quando isAffirmative === true
  3. Faixa salarial deve ser formatada como "R$ X.XXX - R$ Y.YYY" (formato pt-BR)
  4. Etapas do processo devem ser ordenadas por campo order
  5. Etapas com liaAssisted === true exibem indicador visual (ponto cyan)
  6. Badge de status da triagem usa cores semânticas — verde para Ativo, âmbar para Pausado
  7. Tempo estimado da triagem é calculado como soma dos time_limit das perguntas / 60
  8. Canais de comunicação são derivados do screeningConfig.channels
  9. O painel é somente leitura — nenhuma edição direta é permitida

Requisitos Tecnicos:
  Frontend:
    - Componente Vue 3 com Composition API (setup script)
    - Props tipadas via TypeScript interface JobPreviewTabProps
    - Uso de v-chip (Vuetify) para badges de competências e idiomas
    - Benefícios via BenefitBadgeList component com CompanyBenefit model (14 campos), tooltips detalhados e BenefitDetailsSheet
    - Truncamento de texto com v-if/v-else e controle de estado local showFullDescription
    - Formatação de moeda usando Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
    - Pipeline horizontal com flexbox e ícone ChevronRight entre etapas
  Backend:
    - GET /api/v1/jobs/:id — retorna dados completos da vaga incluindo screeningConfig
    - Serializer deve incluir campos: screeningQuestions, screeningConfig, interviewStages, behavioralCompetencies, technicalCompetencies
  Dados:
    - Interface JobPreviewTabProps com campos: title, department, location, workModel, type, level, description, requirements, benefits (CompanyBenefit[] | string[]), languages, salaryRange/salaryMin/salaryMax, bonusRange/bonusMin/bonusMax, interviewStages, behavioralCompetencies, technicalCompetencies, screeningQuestions, screeningConfig, funnel, nps, isAffirmative, affirmativeCriteriaPrimary, affirmativeType, pipelineStages
  Validacoes:
    - Tratar campos undefined/null com fallback para estados vazios
    - Verificar tipo de benefits: array de CompanyBenefit (14 campos) ou string[] legado — usar toCompanyBenefit() para normalizar
    - Tratar salaryRange como objeto ou campos separados salaryMin/salaryMax

Design & Componentes:
  Componentes Existentes:
    - v-chip (Vuetify) para badges de competências e idiomas
    - v-icon para ícones Lucide equivalentes
    - v-card para containers de seção
  Novos Componentes:
    - JobPreviewPanel.vue — componente principal do painel lateral
    - PipelineStagesPreview.vue — pipeline horizontal com chevrons
    - ScreeningStatusBadge.vue — badge de status da triagem (Ativo/Pausado)
    - BenefitBadgeList.vue — badges de benefícios com ícones por categoria, tooltips detalhados (valor, carência, obrigatoriedade, provedor), BenefitDetailsSheet para overflow
  Design Tokens:
    - bg-primary: #FFFFFF
    - border-section: border-gray-100
    - text-heading: text-gray-950 (11px, font-semibold)
    - text-body: text-gray-600 (10px)
    - badge-technical: bg-gray-100 text-gray-600
    - badge-behavioral: bg-purple-50 text-purple-700 border-purple-200
    - badge-required: bg-red-50 text-red-600 border-red-200
    - accent-lia: bg-cyan-400 (ponto de LIA-assisted)
    - badge-active: #A8D5B7
    - badge-paused: #D5BFA8
  Layout:
    - Painel lateral com largura fixa (~380px)
    - Seções empilhadas verticalmente com gap de 16px (space-y-4)
    - Cada seção em card com padding 12px, border arredondada 12px, sombra leve
  Estados:
    - Loading — skeleton placeholder
    - Vazio — mensagens "Nenhuma [item] configurada" em itálico
    - Preenchido — dados renderizados normalmente
    - Descrição expandida/colapsada
  Acessibilidade:
    - Botão "Ver mais"/"Ver menos" com aria-expanded
    - Ícones com aria-label descritivo
    - Contraste WCAG AA para todos os textos
    - Navegação por teclado nos botões interativos

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona uma vaga na tabela
    2. Painel lateral abre à direita com dados da vaga
    3. Seções são renderizadas na ordem definida
    4. Recrutador pode expandir/colapsar descrição longa
    5. Recrutador pode clicar no botão para abrir visualização completa
  Estados de Botoes:
    - "Ver mais" — visível quando descrição > 300 chars e está colapsada
    - "Ver menos" — visível quando descrição está expandida
    - Botão de expansão — sempre visível no topo ou rodapé do painel
  Validacoes Inline:
    - Nenhuma (componente read-only)
  Mensagens de Feedback:
    - "Nenhuma descrição adicionada" — quando description vazio
    - "Nenhuma competência técnica configurada" — quando technicalCompetencies vazio
    - "Nenhuma competência comportamental configurada" — quando behavioralCompetencies vazio
    - "Nenhum idioma configurado" — quando languages vazio
    - "Faixa salarial não informada" — quando salaryMin e salaryMax vazios
    - "Nenhuma etapa configurada" — quando interviewStages e pipelineStages vazios
    - "Nenhum canal configurado" — quando nenhum canal habilitado

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Componente JobPreviewPanel.vue implementado com todas as 10 seções
  - [ ] Props tipadas via interface TypeScript
  - [ ] Truncamento de descrição funcionando com "Ver mais"/"Ver menos"
  - [ ] Formatação de moeda em pt-BR
  - [ ] Pipeline horizontal com chevrons e indicador LIA-assisted
  - [ ] Seção de Ações Afirmativas condicional
  - [ ] Badge de status da triagem com cores semânticas
  - [ ] Campos vazios com mensagens de fallback
  - [ ] Testes unitários com cobertura > 80%
  - [ ] Code review aprovado
  - [ ] Design tokens aplicados conforme Design System v4.1

Criterios de Aceitacao:
  - [ ] Ao selecionar uma vaga na tabela, o painel lateral exibe todas as 10 seções na ordem correta
  - [ ] Descrições > 300 caracteres são truncadas com botão "Ver mais"
  - [ ] Competências técnicas aparecem como badges cinza
  - [ ] Competências comportamentais aparecem como badges roxos
  - [ ] Idiomas mostram nível e badge "Obrigatório" quando required === true
  - [ ] Salário é formatado como "R$ X.XXX - R$ Y.YYY"
  - [ ] Etapas do processo aparecem em pipeline horizontal com chevrons
  - [ ] Etapas LIA-assisted têm ponto cyan visível
  - [ ] Seção de Ações Afirmativas só aparece quando isAffirmative === true
  - [ ] Badge de triagem mostra "Ativo" (verde) ou "Pausado" (âmbar)
  - [ ] Botão de expansão navega para a visualização completa da vaga

Arquivos de Referencia (Prototipo Replit):
  - JobPreviewTab.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/jobs/JobPreviewTab.tsx
  - jobsPageTypes.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/jobs/jobsPageTypes.ts
  - BenefitBadgeList.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/benefits/BenefitBadgeList.tsx
  - BenefitDetailsSheet.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/benefits/BenefitDetailsSheet.tsx
  - types/benefits.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/types/benefits.ts
  - useCompanyBenefits.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useCompanyBenefits.ts

Nota MVP (v1):
  - MVP v1: Todas as 10 seções implementadas em modo read-only
  - Pós-MVP: Ações rápidas inline (ex: pausar triagem direto do preview)

Integracoes e Impactos:
  Componentes Afetados:
    - Tabela de Vagas — deve emitir evento de seleção para abrir o painel
    - Layout da página de Vagas — deve acomodar painel lateral
  Vinculacoes:
    - CFG-002 a CFG-007 — dados exibidos no preview são editados nestes cards
    - CFG-011 — badge de status de triagem usa mesma lógica de cores
    - CFG-012 — status de triagem reflete impactos automáticos
  Comportamentos Automaticos:
    - Atualização do preview ao salvar alterações nas configurações da vaga

Dados e Estado:
  Interfaces:
    - "JobPreviewTabProps { job: Job, pipelineStages?: PipelineStage[] }"
    - "PipelineStage { id: string, name: string, count: number, color?: string, liaAssisted?: boolean }"
  Campos:
    - title, department, location, workModel, type, level (read-only display)
    - description (com truncamento)
    - requirements/technicalCompetencies (badges)
    - behavioralCompetencies (badges roxos)
    - languages (com level e required)
    - salaryMin, salaryMax, bonusMin, bonusMax (formatados)
    - benefits (CompanyBenefit[] via BenefitBadgeList — 8 categorias com ícones, tooltips com valor/carência/badges obrigatório/destaque/desconto/provedor)
    - interviewStages/pipelineStages (pipeline visual)
    - screeningQuestions (contagem)
    - screeningConfig (status, channels, scheduling)
    - isAffirmative, affirmativeCriteriaPrimary, affirmativeType
  Estados do Componente:
    - showFullDescription: boolean (controle do truncamento)
    - Nenhum outro estado mutável (componente read-only)

QA/Teste:
  Cenarios de Teste:
    - "Renderizar preview com todos os campos preenchidos — todas as 10 seções visíveis"
    - "Renderizar preview com campos vazios — mensagens de fallback corretas"
    - "Truncar descrição > 300 caracteres e expandir/colapsar com botão"
    - "Formatar salário como R$ com separador de milhar pt-BR"
    - "Exibir pipeline horizontal com 5+ etapas sem overflow visual"
    - "Mostrar ponto cyan apenas em etapas com liaAssisted === true"
    - "Ocultar seção Ações Afirmativas quando isAffirmative === false"
    - "Exibir badge 'Ativo' verde quando triagem habilitada"
    - "Exibir badge 'Pausado' âmbar quando triagem desabilitada"
    - "Calcular tempo estimado da triagem corretamente"
  Casos Edge:
    - "Descrição com exatamente 300 caracteres — não deve truncar"
    - "Descrição com 301 caracteres — deve truncar"
    - "Vaga sem salaryMin nem salaryMax — exibir 'Faixa salarial não informada'"
    - "Vaga com salaryRange objeto vs campos separados"
    - "benefits como array de strings legado vs array de CompanyBenefit (14 campos) — toCompanyBenefit() normaliza"
    - "interviewStages vazio mas pipelineStages preenchido — usar pipelineStages"
    - "screeningConfig undefined — usar defaults"
  Checklist de Regressao:
    - [ ] Preview continua funcionando após alterações em JobEditTab
    - [ ] Layout não quebra em telas < 1280px
    - [ ] Dados refletem salvamentos recentes na aba de configuração
    - [ ] Navegação por teclado funcional em todos os botões

Bitbucket Commit:
  Branch: feature/CFG-001-job-preview-panel
  Commit Pattern: "[CFG-001] feat: implementar painel lateral de preview da vaga"
  PR Checklist:
    - [ ] Componente Vue 3 com TypeScript
    - [ ] Props tipadas e documentadas
    - [ ] Testes unitários (Vitest)
    - [ ] Design tokens aplicados
    - [ ] Responsividade verificada
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Estou implementando o painel lateral de preview de vaga na Plataforma LIA.
    Este componente aparece ao lado da tabela de vagas quando uma vaga é selecionada.

    Stack: Vue 3 (Composition API + script setup) + Nuxt 3 + Vuetify 3 (frontend), Ruby on Rails 7.x (backend).

    Referência do protótipo Replit (React/Next.js):
    - plataforma-lia/src/components/jobs/JobPreviewTab.tsx

    Implementar componente JobPreviewPanel.vue com 10 seções na ordem:
    1. Descrição da Vaga (truncamento > 300 chars, "Ver mais"/"Ver menos")
    2. Competências Técnicas (v-chip cinza)
    3. Competências Comportamentais (v-chip roxo)
    4. Idiomas (nível + badge "Obrigatório")
    5. Remuneração e Benefícios (R$ formatado, bônus, badges)
    6. Etapas do Processo (pipeline horizontal com v-icon mdi-chevron-right, ponto cyan para LIA)
    7. Ações Afirmativas (condicional, bg purple)
    8. Fluxo de Triagem WSI (contagem perguntas, tempo estimado, badge Ativo/Pausado)
    9. Agendamento (score mínimo, calendário, horários, duração)
    10. Canais de Comunicação (badges canal, score, timeout, retries, fallback)

    Regras de negócio:
    - Seção Ações Afirmativas só aparece se isAffirmative === true
    - Formatar moeda: Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
    - Badge triagem: verde (#A8D5B7) para Ativo, âmbar (#D5BFA8) para Pausado
    - Campos vazios: mensagem italic "Nenhuma [X] configurada"
    - liaAssisted: span com bg-cyan-400 w-1.5 h-1.5 rounded-full

    Design System: Design System LIA v4.1
    Tokens: accent-primary #60BED1, bg-primary #FFFFFF, text-primary #111827

    Critérios de aceite:
    - [ ] 10 seções renderizadas na ordem
    - [ ] Truncamento com Ver mais/Ver menos
    - [ ] Pipeline horizontal com chevrons
    - [ ] Badges com cores corretas
    - [ ] Campos vazios com fallback
    - [ ] Testes unitários com Vitest
```

---

### CFG-002: Tab Configurações da Vaga — Informações Gerais

```yaml
Titulo: "[FULL-STACK] Tab Configurações da Vaga — Informações Gerais"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 8
Prioridade: Crítica
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-001

Descricao: |
  Seção "Informações Gerais" dentro da tab Configurações da vaga.
  Sidebar esquerda com 4 seções de configuração da vaga (Info Gerais, Pessoas, Processo Seletivo, Remuneração)
  + 3 seções de configuração de triagem abaixo (Configurações do Roteiro, Descrição do Cargo, Perguntas de Triagem).

  Campos organizados em grupos semânticos:
  - Gestão: status, prioridade, urgencyLevel
  - Identificação: title, department
  - Classificação: level, workModel, type
  - Prazos: openDate, deadline, deadlineScreening, deadlineShortlist, deadlineClosing
  - Descrição: description (textarea)
  - Idiomas: array com language/level/required
  - Ações Afirmativas: isAffirmative (toggle), affirmativeCriteriaPrimary, affirmativeCriteriaSecondary, affirmativeDescription, affirmativeDocumentRequired, affirmativeDocumentTypes
  - Visibilidade: visibility, isConfidential, maskedCompanyName
  - Canais: publishedLinkedIn, publishedWebsite, publishedIndeed

  ScreeningBadge (ícone de filtro cyan) nos campos que impactam a triagem: workModel, type, location, languages, isAffirmative.
  Modos Read/Edit com botões Editar/Salvar/Cancelar.
  formBackupRef para restauração ao cancelar.
  Indicador de completude da seção (threshold de 30%).

Historia de Usuario: |
  Como recrutador, eu quero editar as informações gerais de uma vaga em um formulário organizado
  para configurar todos os dados principais da posição de forma eficiente.

Regras de Negocio:
  1. SWITCH_FIELDS (publishedLinkedIn, publishedWebsite, publishedIndeed, isConfidential, isAffirmative, affirmativeDocumentRequired) usam toggle switch ao invés de input text
  2. Campos com ScreeningBadge (workModel, type, location, languages, isAffirmative) exibem ícone de filtro cyan indicando impacto na triagem
  3. Ao cancelar edição, restaurar valores do formBackupRef
  4. Indicador de completude mostra porcentagem de campos preenchidos (threshold 30% para "completo")
  5. Campos de data (openDate, deadline, etc.) usam date picker
  6. Seção de Ações Afirmativas se expande condicionalmente quando isAffirmative === true
  7. Campos de idiomas permitem adicionar/remover entradas com language, level e required
  8. Status da vaga deve verificar impacto na triagem antes de alterar (CFG-012)
  9. Ao salvar, chamar onSaveSection com sectionId e lista de campos

Requisitos Tecnicos:
  Frontend:
    - Componente Vue 3 com Composition API
    - Sidebar com v-list para navegação entre seções
    - Formulário com v-text-field, v-select, v-textarea, v-switch (Vuetify 3)
    - Estado editingSection controlando modo read/edit
    - formBackupRef usando ref() para snapshot dos valores antes da edição
    - ScreeningBadge como componente inline com v-icon mdi-filter e tooltip
    - Indicador de completude usando computed property com countFilledFields
  Backend:
    - PUT /api/v1/jobs/:id — atualizar campos da vaga
    - Request body: JSON com campos da seção info-geral
    - Validação de campos obrigatórios: title, department
    - Serializer com todos os campos do SECTIONS array
  Dados:
    - SECTIONS array com id "info-geral", campos: title, department, location, workModel, type, level, status, priority, urgencyLevel, openDate, deadline, deadlineScreening, deadlineShortlist, deadlineClosing, visibility, isConfidential, maskedCompanyName, isAffirmative, affirmativeCriteriaPrimary, affirmativeCriteriaSecondary, affirmativeDescription, affirmativeDocumentRequired, affirmativeDocumentTypes, description, targetAudience, targetSector, targetSegment, languages, publishedLinkedIn, publishedWebsite, publishedIndeed
    - SWITCH_FIELDS: publishedLinkedIn, publishedWebsite, publishedIndeed, isConfidential, isAffirmative, affirmativeDocumentRequired
  Validacoes:
    - title: obrigatório, min 3 caracteres
    - department: obrigatório
    - Datas: formato ISO 8601, deadline >= openDate
    - languages: cada item deve ter language (string) e level (string)

Design & Componentes:
  Componentes Existentes:
    - v-text-field, v-select, v-textarea, v-switch, v-btn (Vuetify 3)
    - v-list para sidebar de navegação
  Novos Componentes:
    - JobEditTab.vue — componente principal da tab de configurações
    - JobSectionSidebar.vue — sidebar com 7 seções navegáveis
    - ScreeningBadge.vue — ícone de filtro cyan com tooltip
    - LanguageFieldArray.vue — campo dinâmico para idiomas
    - AffirmativeSection.vue — seção condicional de ações afirmativas
  Design Tokens:
    - input: px-3 py-2, text-12px, border-gray-200, rounded-xl
    - label: text-11px, font-semibold, text-gray-500, uppercase, tracking-wider
    - group-header: text-11px, font-semibold, text-gray-500, uppercase
    - screening-badge: text-cyan-500 (ícone Filter w-3 h-3)
    - active-section: bg-gray-50, border border-gray-900
    - completion-done: text-emerald-500 (CheckCircle2)
    - completion-pending: text-gray-300 (Circle)
  Layout:
    - Sidebar 220px fixa à esquerda
    - Conteúdo do formulário flex-1 à direita
    - Grupos de campos com header semântico e espaçamento vertical
  Estados:
    - Read mode — campos desabilitados, botão "Editar" visível
    - Edit mode — campos habilitados, botões "Salvar" e "Cancelar" visíveis
    - Saving — botão "Salvando..." com ícone Loader2 animado
    - Section selected — destacada na sidebar com borda
    - Completion indicator — CheckCircle2 verde ou Circle cinza
  Acessibilidade:
    - Labels associados a inputs via for/id
    - ScreeningBadge com title/aria-label "Usado na triagem da LIA"
    - Sidebar navegável por teclado
    - Focus trapping no formulário ativo

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa a tab Configurações de uma vaga
    2. Sidebar mostra 7 seções com indicadores de completude
    3. Seção "Informações Gerais" é selecionada por padrão
    4. Formulário exibe campos em modo read-only
    5. Recrutador clica "Editar" para habilitar edição
    6. Recrutador preenche/altera campos
    7. Recrutador clica "Salvar" para persistir ou "Cancelar" para restaurar
  Estados de Botoes:
    - "Editar" — visível em read mode, estilo outline
    - "Salvar" — visível em edit mode, estilo primary (bg-gray-900 text-white)
    - "Cancelar" — visível em edit mode, estilo outline
    - "Salvando..." — durante save, desabilitado com Loader2
  Validacoes Inline:
    - title vazio — borda vermelha com mensagem "Título é obrigatório"
    - deadline < openDate — mensagem "Prazo deve ser posterior à data de abertura"
  Mensagens de Feedback:
    - Toast sucesso "Informações gerais salvas com sucesso"
    - Toast erro "Erro ao salvar. Tente novamente."
    - Badge "X de Y campos" no header da seção

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Componente JobEditTab.vue implementado com sidebar e formulário
  - [ ] 7 seções navegáveis na sidebar com indicadores de completude
  - [ ] Todos os campos do SECTIONS "info-geral" renderizados
  - [ ] Modos Read/Edit com Editar/Salvar/Cancelar
  - [ ] formBackupRef restaura valores ao cancelar
  - [ ] ScreeningBadge nos campos que impactam triagem
  - [ ] SWITCH_FIELDS renderizados como toggles
  - [ ] Campos de idiomas dinâmicos (add/remove)
  - [ ] Seção Ações Afirmativas condicional
  - [ ] API PUT /api/v1/jobs/:id integrada
  - [ ] Testes unitários com cobertura > 80%
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] Sidebar exibe 4 seções de vaga + 3 de triagem com ícones e descrição
  - [ ] Seção ativa destacada com borda na sidebar
  - [ ] Indicador de completude (CheckCircle2 verde / Circle cinza) correto
  - [ ] Campos em modo read-only por padrão
  - [ ] Botão "Editar" habilita todos os campos da seção
  - [ ] Botão "Cancelar" restaura valores originais via formBackupRef
  - [ ] Botão "Salvar" persiste dados e retorna para modo read-only
  - [ ] ScreeningBadge visível em workModel, type, location, languages, isAffirmative
  - [ ] Toggle switches funcionam para SWITCH_FIELDS
  - [ ] Contador "X de Y campos" atualiza em tempo real
  - [ ] Seção Ações Afirmativas expande ao ativar toggle isAffirmative

Arquivos de Referencia (Prototipo Replit):
  - JobEditTab.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/jobs/JobEditTab.tsx

Nota MVP (v1):
  - MVP v1: EDITÁVEL no MVP — todos os campos de Informações Gerais são editáveis
  - Pós-MVP: Validação avançada de campos, auto-save com debounce

Integracoes e Impactos:
  Componentes Afetados:
    - Preview da Vaga (CFG-001) — dados alterados refletem no preview
    - Perguntas Derivadas (CFG-007) — campos com ScreeningBadge geram perguntas automáticas
    - Status de Triagem (CFG-011) — mudança de status da vaga impacta triagem
  Vinculacoes:
    - CFG-003 — seção "Processo Seletivo" acessível pela mesma sidebar
    - CFG-004 — seção "Pessoas" e "Remuneração" acessíveis pela mesma sidebar
    - CFG-005 a CFG-007 — seções de triagem acessíveis pela sidebar
    - CFG-012 — mudança de status dispara lógica de impacto na triagem
  Comportamentos Automaticos:
    - Alterar workModel, type, location, languages ou isAffirmative regenera perguntas derivadas (CFG-007/CFG-012)
    - Alterar status da vaga pode impactar status da triagem (CFG-012)

Dados e Estado:
  Interfaces:
    - "JobEditTabProps { jobEditForm: Record<string, any>, setJobEditForm: Function, onSaveSection: Function, savingSection: string | null, companyDefaults?: CompanyDefaults, job?: Job, onJobUpdate?: Function, onFormUpdate?: Function }"
    - "Section { id: string, title: string, icon: Component, description: string, fields: string[] }"
  Campos:
    - title (text), department (text), location (text), workModel (select), type (select), level (select)
    - status (select), priority (select), urgencyLevel (select 1-5)
    - openDate (date), deadline (date), deadlineScreening (date), deadlineShortlist (date), deadlineClosing (date)
    - description (textarea)
    - languages (array: language/level/required)
    - isAffirmative (switch), affirmativeCriteriaPrimary (select), affirmativeCriteriaSecondary (text), affirmativeDescription (textarea), affirmativeDocumentRequired (switch), affirmativeDocumentTypes (text)
    - visibility (select), isConfidential (switch), maskedCompanyName (text)
    - publishedLinkedIn (switch), publishedWebsite (switch), publishedIndeed (switch)
  Estados do Componente:
    - activeSection: string ("info-geral" default)
    - editingSection: string | null
    - formBackupRef: Record<string, any> | null
    - savingSection: string | null

QA/Teste:
  Cenarios de Teste:
    - "Alternar entre seções na sidebar mantém dados não salvos"
    - "Editar e salvar informações gerais persiste no backend"
    - "Cancelar edição restaura valores originais"
    - "ScreeningBadge aparece nos 5 campos corretos"
    - "Toggle isAffirmative expande/colapsa seção condicional"
    - "Adicionar e remover idiomas funciona corretamente"
    - "Indicador de completude atualiza ao preencher/limpar campos"
    - "Salvar com campos obrigatórios vazios mostra erro inline"
  Casos Edge:
    - "Navegar para outra seção durante edição — deve manter/alertar sobre dados não salvos"
    - "Salvar com network error — exibir toast de erro e manter modo edit"
    - "Campos SWITCH_FIELDS sempre contam como preenchidos no indicador de completude"
    - "Descrição muito longa (> 5000 chars) — textarea não trava"
    - "Múltiplos idiomas com mesmo language — permitir"
  Checklist de Regressao:
    - [ ] Sidebar navegação funciona após salvar
    - [ ] Preview (CFG-001) reflete dados salvos
    - [ ] Perguntas derivadas regeneram após alterar campos de triagem
    - [ ] Status change não quebra com screeningConfig undefined

Bitbucket Commit:
  Branch: feature/CFG-002-job-edit-info-gerais
  Commit Pattern: "[CFG-002] feat: implementar tab configurações da vaga — informações gerais"
  PR Checklist:
    - [ ] Componente Vue 3 com TypeScript
    - [ ] Sidebar com 7 seções e indicadores de completude
    - [ ] Formulário com todos os campos mapeados
    - [ ] Modos Read/Edit implementados
    - [ ] ScreeningBadge nos campos corretos
    - [ ] Testes unitários (Vitest)
    - [ ] API integration testada
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar a seção "Informações Gerais" da tab Configurações da Vaga na Plataforma LIA.
    Este componente inclui uma sidebar de navegação com 7 seções e um formulário editável.

    Stack: Vue 3 (Composition API + script setup) + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência do protótipo Replit (React/Next.js):
    - plataforma-lia/src/components/jobs/JobEditTab.tsx (SECTIONS array, linhas 55-84)

    Criar JobEditTab.vue com:
    1. Sidebar 220px com v-list:
       - 4 seções vaga: Info Gerais (Briefcase), Pessoas (Users), Processo Seletivo (ListOrdered), Remuneração (DollarSign)
       - Divisor visual
       - 3 seções triagem: Configurações do Roteiro (Settings2), Descrição do Cargo (FileText), Perguntas (ListChecks)
       - Indicador completude: CheckCircle2 verde (>= 30% preenchido) ou Circle cinza
    2. Formulário principal (flex-1):
       - Header com ícone, título, descrição, contador "X de Y campos", botões Editar/Salvar/Cancelar
       - Campos agrupados: Gestão, Identificação, Classificação, Prazos, Descrição, Idiomas, Ações Afirmativas, Visibilidade, Canais
       - SWITCH_FIELDS: publishedLinkedIn, publishedWebsite, publishedIndeed, isConfidential, isAffirmative, affirmativeDocumentRequired → v-switch
       - ScreeningBadge: ícone mdi-filter cyan nos campos workModel, type, location, languages, isAffirmative com tooltip
    3. Lógica:
       - formBackupRef para restaurar ao cancelar
       - countFilledFields ignora SWITCH_FIELDS (sempre conta como preenchido)
       - PUT /api/v1/jobs/:id ao salvar

    Design System: Design System LIA v4.1
    Tokens: input rounded-xl, text-12px, label uppercase 11px
```

---

### CFG-003: Tab Configurações da Vaga — Processo Seletivo

```yaml
Titulo: "[FULL-STACK] Tab Configurações da Vaga — Processo Seletivo"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 5
Prioridade: Crítica
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-002, CFG-008

Descricao: |
  Seção "Processo Seletivo" da tab Configurações da vaga.
  Lista de etapas do recrutamento com funcionalidades de CRUD e reordenação.
  Cada etapa contém: stageName, stageCategory (system/default/custom), order, type, slaDays, liaAssisted.
  Herda do pipeline da empresa (getCompanyPipelineStages()) como default quando não há etapas configuradas.

Historia de Usuario: |
  Como recrutador, eu quero configurar as etapas do processo seletivo de uma vaga
  para personalizar o pipeline de recrutamento conforme as necessidades da posição.

Regras de Negocio:
  1. Etapas do sistema (stageCategory === 'system') não podem ser renomeadas nem removidas
  2. Nova etapa é inserida antes da etapa "Proposta" se existir
  3. Remoção bloqueada para etapas com isRemovable === false
  4. Reordenação bloqueada para etapas com isReorderable === false ou stageCategory === 'system'
  5. Se rawStages vazio, usar pipeline da empresa como fallback via getCompanyPipelineStages()
  6. Badges de categoria: Sistema (cinza, Lock), Padrão (azul, Target), Custom (âmbar, Settings)
  7. Tipos de etapa: Entrevista, Teste, Manual, Automatizado, Híbrido, Personalizado
  8. Toggle ativo/inativo por etapa (exceto system)
  9. Orders são recalculados após add/remove/reorder (sequencial 1, 2, 3...)

Requisitos Tecnicos:
  Frontend:
    - Lista de etapas com v-list-item iterável
    - Botões de reordenação (setas up/down) com v-btn icon
    - Badge de categoria com v-chip e ícone correspondente
    - Select de tipo de etapa com v-select
    - Input de SLA (dias) com v-text-field type="number"
    - Botão "Adicionar etapa" com lógica de inserção antes de "Proposta"
    - Botão remover com confirmação
    - Toggle ativo/inativo com v-switch
  Backend:
    - PUT /api/v1/jobs/:id — campo interviewStages como array de objetos
    - Validação de integridade: orders sequenciais, stageCategory válido
  Dados:
    - "InterviewStage { stageName: string, stageCategory: 'system' | 'default' | 'custom', order: number, type: string, slaDays?: number, liaAssisted?: boolean, isEditable?: boolean, isRemovable?: boolean, isReorderable?: boolean }"
    - stageTypeLabels: { interview: 'Entrevista', test: 'Teste', manual: 'Manual', automated: 'Automatizado', hybrid: 'Híbrido', custom: 'Personalizado' }
  Validacoes:
    - stageName obrigatório (min 2 caracteres) para etapas editáveis
    - slaDays >= 1
    - Máximo 20 etapas por vaga

Design & Componentes:
  Componentes Existentes:
    - v-list, v-list-item, v-chip, v-btn, v-select, v-switch, v-text-field (Vuetify 3)
  Novos Componentes:
    - ProcessoSeletivoSection.vue — seção completa
    - StageListItem.vue — item individual de etapa com controles
    - StageCategoryBadge.vue — badge com ícone e cor por categoria
  Design Tokens:
    - badge-system: text-gray-400 bg-gray-50 (Lock icon)
    - badge-default: text-blue-500 bg-blue-50 (Target icon)
    - badge-custom: text-amber-500 bg-amber-50 (Settings icon)
    - grip-handle: GripVertical icon text-gray-300
  Layout:
    - Lista vertical de etapas com drag handles à esquerda
    - Cada item: grip | nome | badge categoria | tipo | SLA | toggle | ações
    - Botão "Adicionar etapa" no final da lista
  Estados:
    - Read mode — etapas visíveis sem controles de edição
    - Edit mode — controles de edição visíveis (renomear, reordenar, remover, toggle)
    - Etapa system — controles de edição desabilitados/ocultos
  Acessibilidade:
    - Botões de reordenação com aria-label "Mover etapa para cima"/"Mover etapa para baixo"
    - Botão remover com aria-label "Remover etapa [nome]"
    - Lista com role="list" e items com role="listitem"

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador navega para seção "Processo Seletivo" na sidebar
    2. Lista de etapas é exibida (herdada da empresa ou configurada)
    3. Recrutador clica "Editar" para habilitar edição
    4. Recrutador pode adicionar, remover, renomear, reordenar etapas
    5. Recrutador salva alterações
  Estados de Botoes:
    - "Adicionar etapa" — visível em edit mode, inserção antes de "Proposta"
    - Setas up/down — desabilitadas para etapas system ou nas extremidades
    - Trash — desabilitado para etapas system ou isRemovable === false
  Validacoes Inline:
    - stageName vazio ao salvar — destaque vermelho
  Mensagens de Feedback:
    - Toast "Processo seletivo salvo com sucesso"
    - Toast "Não é possível remover etapa do sistema"

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Lista de etapas renderizada com todos os campos
  - [ ] Badges de categoria com ícones e cores corretas
  - [ ] CRUD de etapas funcionando (add/edit/remove/reorder)
  - [ ] Etapas system protegidas contra edição/remoção
  - [ ] Herança do pipeline da empresa como fallback
  - [ ] Toggle ativo/inativo por etapa
  - [ ] Orders recalculados após operações
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] Etapas exibidas na ordem correta com badges de categoria
  - [ ] Etapas system não podem ser renomeadas, removidas ou reordenadas
  - [ ] Nova etapa inserida antes de "Proposta"
  - [ ] Reordenação funciona com botões up/down
  - [ ] Toggle ativo/inativo funciona para etapas não-system
  - [ ] Sem etapas configuradas, pipeline da empresa é usado como default
  - [ ] Orders são sequenciais após qualquer operação

Arquivos de Referencia (Prototipo Replit):
  - JobEditTab.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/jobs/JobEditTab.tsx

Nota MVP (v1):
  - MVP v1: EDITÁVEL no MVP — CRUD completo de etapas
  - Pós-MVP: Drag-and-drop para reordenação, templates de pipeline

Integracoes e Impactos:
  Componentes Afetados:
    - Preview da Vaga (CFG-001) — pipeline horizontal reflete etapas configuradas
  Vinculacoes:
    - CFG-008 — pipeline da empresa serve como template default
    - CFG-012 — etapas com liaAssisted são usadas na lógica de triagem
  Comportamentos Automaticos:
    - Sem etapas configuradas, herda automaticamente do pipeline da empresa

Dados e Estado:
  Interfaces:
    - "InterviewStage { stageName: string, stageCategory: 'system' | 'default' | 'custom', order: number, type: string, slaDays?: number, liaAssisted?: boolean, name?: string, isEditable?: boolean, isRemovable?: boolean, isReorderable?: boolean }"
  Campos:
    - stageName (text input editável), stageCategory (badge read-only), order (auto), type (select), slaDays (number), liaAssisted (indicator)
  Estados do Componente:
    - stages: InterviewStage[] — lista de etapas da vaga
    - companyPipeline usado como fallback quando stages vazio

QA/Teste:
  Cenarios de Teste:
    - "Adicionar etapa custom antes de Proposta"
    - "Remover etapa custom — orders recalculados"
    - "Tentar remover etapa system — bloqueado"
    - "Reordenar etapas — orders atualizados sequencialmente"
    - "Vaga sem etapas — herda pipeline da empresa"
    - "Toggle ativo/inativo em etapa custom"
  Casos Edge:
    - "Vaga sem etapas e empresa sem pipeline — lista vazia"
    - "20 etapas (máximo) — botão adicionar desabilitado"
    - "Etapa com nome duplicado — permitir"
    - "Salvar com stageName vazio — erro inline"
  Checklist de Regressao:
    - [ ] Preview (CFG-001) reflete etapas salvas
    - [ ] Pipeline da empresa (CFG-008) serve como fallback
    - [ ] Dados persistem após reload

Bitbucket Commit:
  Branch: feature/CFG-003-processo-seletivo
  Commit Pattern: "[CFG-003] feat: implementar seção processo seletivo com CRUD de etapas"
  PR Checklist:
    - [ ] CRUD de etapas implementado
    - [ ] Proteção de etapas system
    - [ ] Herança do pipeline da empresa
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar seção "Processo Seletivo" na tab Configurações da Vaga.
    Lista editável de etapas do pipeline de recrutamento.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência: plataforma-lia/src/components/jobs/JobEditTab.tsx (linhas 212-297)

    Implementar:
    - Lista de etapas: stageName, stageCategory (system/default/custom), order, type, slaDays, liaAssisted
    - Badges: Sistema (cinza, Lock), Padrão (azul, Target), Custom (âmbar, Settings)
    - Tipos: { interview: 'Entrevista', test: 'Teste', manual: 'Manual', automated: 'Automatizado', hybrid: 'Híbrido', custom: 'Personalizado' }
    - Etapas system: não podem ser renomeadas/removidas/reordenadas
    - Adicionar: inserir antes de "Proposta"
    - Reordenar: botões up/down, recalcular orders
    - Fallback: getCompanyPipelineStages() quando rawStages vazio
    - Toggle ativo/inativo (exceto system)
```

---

### CFG-004: Tab Configurações da Vaga — Pessoas e Remuneração

```yaml
Titulo: "[FULL-STACK] Tab Configurações da Vaga — Pessoas e Remuneração"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 3
Prioridade: Média
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-002

Descricao: |
  Seções complementares "Pessoas" e "Remuneração" dentro da tab Configurações da vaga.
  Pessoas: campos de recrutador e gestor com nome e email.
  Remuneração: faixa salarial, bônus e lista de benefícios.
  Ambas as seções seguem o mesmo padrão de Read/Edit modes das outras seções.

Historia de Usuario: |
  Como recrutador, eu quero registrar os responsáveis pela vaga e a remuneração oferecida
  para manter as informações organizadas e acessíveis para a equipe.

Regras de Negocio:
  1. Campos de Pessoas: recruiter (nome), recruiterEmail, manager (nome), managerEmail
  2. Campos de Remuneração: salaryMin, salaryMax, bonusMin, bonusMax, benefits (CompanyBenefit[] via useCompanyBenefits hook — single source of truth do menu Configurações > Benefícios)
  3. Emails devem ser validados com formato válido
  4. salaryMin <= salaryMax (quando ambos preenchidos)
  5. bonusMin <= bonusMax (quando ambos preenchidos)
  6. Benefits são carregados via useCompanyBenefits() hook da API /company/benefits (single source of truth)
  7. Cada benefit segue o tipo canônico CompanyBenefit com 14 campos (name, description, category, value_type, value, percentage_value, value_details, seniority_levels, waiting_period_days, is_mandatory, is_active, is_highlighted, is_discount, provider)

Requisitos Tecnicos:
  Frontend:
    - Seção Pessoas: 4 v-text-field (recruiter, recruiterEmail, manager, managerEmail)
    - Seção Remuneração: 4 v-text-field numéricos + benefícios via BenefitBadgeList (read) ou seletor de benefícios da empresa (edit)
    - Benefits carregados via useCompanyBenefits() hook — toggle enable/disable por benefício, agrupados por 8 categorias (health, food, transport, education, financial, quality_life, family, security)
    - Modos Read/Edit como nas demais seções
  Backend:
    - PUT /api/v1/jobs/:id — campos pessoas e remuneração
    - Validação de email no backend
  Dados:
    - "Section { id: 'pessoas', fields: ['recruiter', 'recruiterEmail', 'manager', 'managerEmail'] }"
    - "Section { id: 'remuneracao', fields: ['salaryMin', 'salaryMax', 'bonusMin', 'bonusMax', 'benefits'] }"
    - "CompanyBenefit { name, description, category, value_type, value, percentage_value, value_details, seniority_levels, waiting_period_days, is_mandatory, is_active, is_highlighted, is_discount, provider } — tipo canônico de types/benefits.ts"
    - "JobBenefit extends CompanyBenefit com campo enabled — usado no contexto da vaga"
  Validacoes:
    - Email format: regex ou rules Vuetify
    - salaryMin <= salaryMax
    - bonusMin <= bonusMax
    - Benefits validados no menu Configurações > Benefícios (single source of truth) — na vaga apenas toggle enable/disable

Design & Componentes:
  Componentes Existentes:
    - v-text-field, v-btn (Vuetify 3)
    - BenefitBadgeList (convertido para Vue) — exibição de benefícios em modo read com ícones por categoria e tooltips
    - BenefitDetailsSheet (convertido para Vue) — sheet com detalhes completos dos benefícios
  Novos Componentes:
    - PessoasSection.vue — formulário de pessoas
    - RemuneracaoSection.vue — formulário de remuneração com benefícios
    - BenefitSelector.vue — seletor de benefícios da empresa com toggle enable/disable por benefício, agrupado por 8 categorias (substitui BenefitFieldArray.vue)
  Design Tokens:
    - Mesmo padrão do CFG-002 (inputs, labels, group headers)
  Layout:
    - Campos em grid de 2 colunas (nome + email lado a lado)
    - Remuneração em grid 2x2 (salaryMin/Max, bonusMin/Max)
    - Benefícios em lista vertical com botão add
  Estados:
    - Read mode, Edit mode, Saving (mesmo padrão CFG-002)
  Acessibilidade:
    - Labels associados a todos os inputs
    - Mensagens de erro acessíveis

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona "Pessoas" ou "Remuneração" na sidebar
    2. Formulário exibido em modo read-only
    3. Recrutador edita e salva
  Estados de Botoes:
    - Mesmo padrão Editar/Salvar/Cancelar
  Validacoes Inline:
    - Email inválido — mensagem "Email inválido"
    - salaryMin > salaryMax — mensagem "Valor mínimo deve ser menor que o máximo"
  Mensagens de Feedback:
    - Toast sucesso "Dados salvos com sucesso"

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Seção Pessoas com 4 campos
  - [ ] Seção Remuneração com salário, bônus e benefícios
  - [ ] Validação de email
  - [ ] Validação min <= max para salário e bônus
  - [ ] Benefícios integrados via useCompanyBenefits() hook (single source of truth) com BenefitBadgeList/BenefitSelector
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] Campos de Pessoas exibidos e editáveis
  - [ ] Campos de Remuneração exibidos e editáveis
  - [ ] Email inválido mostra erro inline
  - [ ] salaryMin > salaryMax mostra erro inline
  - [ ] Benefícios carregados da API /company/benefits via useCompanyBenefits() hook, com toggle enable/disable por benefício
  - [ ] Dados persistem após salvar

Arquivos de Referencia (Prototipo Replit):
  - JobEditTab.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/jobs/JobEditTab.tsx
  - BenefitBadgeList.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/benefits/BenefitBadgeList.tsx
  - BenefitDetailsSheet.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/benefits/BenefitDetailsSheet.tsx
  - types/benefits.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/types/benefits.ts
  - useCompanyBenefits.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useCompanyBenefits.ts

Nota MVP (v1):
  - MVP v1: Estrutura presente, edição pós-MVP (pode ser read-only inicialmente)
  - Pós-MVP: Edição completa, busca de recrutadores/gestores por autocomplete

Integracoes e Impactos:
  Componentes Afetados:
    - Preview da Vaga (CFG-001) — remuneração e benefícios exibidos no preview
  Vinculacoes:
    - CFG-002 — compartilha a mesma sidebar de navegação
  Comportamentos Automaticos:
    - Nenhum comportamento automático específico

Dados e Estado:
  Interfaces:
    - "Pessoas: { recruiter: string, recruiterEmail: string, manager: string, managerEmail: string }"
    - "Remuneracao: { salaryMin: number, salaryMax: number, bonusMin: number, bonusMax: number, benefits: JobBenefit[] }"
    - "CompanyBenefit (14 campos canônicos) — tipo base de types/benefits.ts"
    - "JobBenefit extends CompanyBenefit { enabled: boolean } — usado no contexto da vaga"
    - "Backward compat: Benefit = JobBenefit alias, toCompanyBenefit() converte string[] legado"
  Campos:
    - recruiter (text), recruiterEmail (email), manager (text), managerEmail (email)
    - salaryMin (number), salaryMax (number), bonusMin (number), bonusMax (number)
    - benefits (JobBenefit[] via useCompanyBenefits hook — toggle enable/disable, agrupados por 8 categorias)
  Estados do Componente:
    - Mesmo padrão de editingSection/formBackupRef

QA/Teste:
  Cenarios de Teste:
    - "Preencher e salvar dados de Pessoas"
    - "Preencher e salvar dados de Remuneração com benefícios"
    - "Validar email inválido"
    - "Validar salaryMin > salaryMax"
    - "Toggle enable/disable de benefícios carregados via useCompanyBenefits()"
  Casos Edge:
    - "Salvar com todos os campos vazios — permitir (campos opcionais)"
    - "Nenhum benefício configurado no menu Configurações > Benefícios — exibir mensagem e link para configurar"
    - "salaryMin = salaryMax — permitir"
  Checklist de Regressao:
    - [ ] Preview (CFG-001) mostra dados de remuneração atualizados
    - [ ] Sidebar mantém indicador de completude correto

Bitbucket Commit:
  Branch: feature/CFG-004-pessoas-remuneracao
  Commit Pattern: "[CFG-004] feat: implementar seções pessoas e remuneração"
  PR Checklist:
    - [ ] Componentes Vue 3
    - [ ] Validações de email e range
    - [ ] Lista dinâmica de benefícios
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar seções "Pessoas" e "Remuneração" na tab Configurações da Vaga.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência: plataforma-lia/src/components/jobs/JobEditTab.tsx (SECTIONS array, linhas 63-84)

    Seção Pessoas:
    - recruiter (v-text-field), recruiterEmail (v-text-field type=email)
    - manager (v-text-field), managerEmail (v-text-field type=email)
    - Grid 2 colunas (nome + email lado a lado)

    Seção Remuneração:
    - salaryMin, salaryMax (v-text-field type=number, prefix "R$")
    - bonusMin, bonusMax (v-text-field type=number, prefix "R$")
    - benefits: JobBenefit[] via useCompanyBenefits() hook (single source of truth: Configurações > Benefícios da empresa)
    - Read mode: BenefitBadgeList com ícones por categoria, tooltips, BenefitDetailsSheet
    - Edit mode: BenefitSelector com toggle enable/disable por benefício, agrupado por 8 categorias
    - Tipo canônico: CompanyBenefit (14 campos: name, description, category, value_type, value, percentage_value, value_details, seniority_levels, waiting_period_days, is_mandatory, is_active, is_highlighted, is_discount, provider)

    Validações: email format, min <= max
    Nota MVP: pode ser read-only inicialmente, edição completa pós-MVP
```

---

### CFG-005: Tab Configurações da Vaga — Configurações do Roteiro de Triagem

```yaml
Titulo: "[FULL-STACK] Tab Configurações da Vaga — Configurações do Roteiro de Triagem"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 5
Prioridade: Crítica
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-002

Descricao: |
  Sub-seção "Configurações do Roteiro" no painel de configurações de triagem da vaga.
  Configura canais de comunicação, presets de score, timeout, retentativas, agendamento
  e nível de auto-aprovação para a triagem WSI.

  Parâmetros configuráveis:
  - Canais: whatsapp (default on), chat_web (default on), phone (default off)
  - Score presets: rigoroso, recomendado (default), flexível — com display do score mínimo
  - Timeout de resposta: horas (default 48h)
  - Máximo de retentativas: (default 2)
  - Agendamento: toggle habilitado (default true), minScorePreset, calendarProvider (Microsoft default), availableHours (9h-18h default, toggle herdado), interviewDuration (60min default)
  - Preset de auto-aprovação: conservador, recomendado (default), autônomo
  - Dialog de confirmação ao ativar/pausar triagem
  - Indicadores de progresso: configDone, jdDone, questionsDone (3 indicadores)

Historia de Usuario: |
  Como recrutador, eu quero configurar os parâmetros do roteiro de triagem
  para controlar como a LIA conduz as entrevistas de triagem com os candidatos.

Regras de Negocio:
  1. Canais são toggles independentes — pelo menos 1 deve estar ativo
  2. Score presets mapeiam para valores numéricos de score mínimo
  3. Timeout mínimo 1 hora, máximo 168 horas (7 dias)
  4. Retentativas mínimo 0, máximo 5
  5. Ao ativar/pausar triagem, exibir dialog de confirmação
  6. Indicadores de progresso: configDone (canais/settings/scheduling configurados), jdDone (descrição preenchida), questionsDone (perguntas adicionadas)
  7. progressCount = contagem de indicadores true (0-3)
  8. Agendamento herda horários da empresa quando toggle herdado ativo
  9. Auto-aprovação define nível de autonomia da LIA

Requisitos Tecnicos:
  Frontend:
    - 3 v-switch para canais (whatsapp, chat_web, phone)
    - v-btn-toggle ou v-radio-group para score presets
    - v-text-field type="number" para timeout e retentativas
    - Seção de agendamento com v-switch (enabled), v-select (calendarProvider), v-text-field (hours, duration)
    - v-btn-toggle para auto-approval preset
    - v-dialog para confirmação de ativar/pausar
    - 3 indicadores de progresso (ícones)
  Backend:
    - PUT /api/v1/jobs/:id/screening-config — salvar configurações de triagem
    - GET /api/v1/jobs/:id/screening-config — buscar configurações
  Dados:
    - "ScreeningConfig { channels: { whatsapp: { enabled: boolean }, chat_web: { enabled: boolean }, phone: { enabled: boolean } }, settings: { minScorePreset: string, timeoutHours: number, maxRetries: number, autoApprovalPreset: string }, scheduling: { enabled: boolean, minScorePreset: string, calendarProvider: string, availableHours: string, availableHoursInherited: boolean, interviewDuration: number } }"
  Validacoes:
    - Pelo menos 1 canal ativo
    - timeoutHours: 1-168
    - maxRetries: 0-5
    - interviewDuration: 15-180 minutos

Design & Componentes:
  Componentes Existentes:
    - v-switch, v-text-field, v-select, v-btn-toggle, v-dialog (Vuetify 3)
  Novos Componentes:
    - ScreeningConfigSection.vue — seção completa de configurações
    - ChannelToggles.vue — grupo de toggles de canais
    - ScorePresetSelector.vue — seletor de preset de score
    - SchedulingConfig.vue — configuração de agendamento
    - ScreeningProgressIndicator.vue — 3 indicadores de progresso
  Design Tokens:
    - toggle-active: bg-green-500
    - preset-selected: bg-gray-900 text-white
    - progress-done: text-emerald-500
    - progress-pending: text-gray-300
  Layout:
    - Grupos de configuração empilhados verticalmente
    - Canais em linha horizontal com toggles
    - Presets em botões de grupo horizontal
    - Agendamento em grid 2 colunas
  Estados:
    - Read mode, Edit mode (padrão CFG-002)
    - Dialog de confirmação ativar/pausar
    - Indicadores de progresso (0/3, 1/3, 2/3, 3/3)
  Acessibilidade:
    - Toggles com labels descritivos
    - Dialog com focus trapping
    - Presets com aria-pressed

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona "Configurações do Roteiro" na sidebar de triagem
    2. Configurações atuais exibidas em read mode
    3. Recrutador clica "Editar Configurações"
    4. Recrutador ajusta canais, presets, timeout, agendamento
    5. Recrutador salva alterações
  Estados de Botoes:
    - "Editar Configurações" — visível em read mode
    - "Salvar" / "Cancelar" — visíveis em edit mode
    - "Ativar Triagem" / "Pausar Triagem" — toggle com dialog de confirmação
  Validacoes Inline:
    - Todos os canais desativados — mensagem "Pelo menos um canal deve estar ativo"
    - Timeout fora do range — mensagem "Valor entre 1 e 168 horas"
  Mensagens de Feedback:
    - Toast "Configurações de triagem salvas com sucesso"
    - Dialog "Deseja ativar a triagem para esta vaga?"
    - Dialog "Deseja pausar a triagem desta vaga?"

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Toggles de canais funcionando
  - [ ] Seletor de presets de score implementado
  - [ ] Configuração de timeout e retentativas
  - [ ] Seção de agendamento completa
  - [ ] Preset de auto-aprovação
  - [ ] Dialog de confirmação para ativar/pausar
  - [ ] 3 indicadores de progresso
  - [ ] API integrada
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] 3 canais configuráveis via toggle (whatsapp on, chat_web on, phone off por padrão)
  - [ ] Score preset selecionável (rigoroso/recomendado/flexível)
  - [ ] Timeout editável em horas (default 48)
  - [ ] Retentativas editáveis (default 2)
  - [ ] Agendamento configurável com todos os parâmetros
  - [ ] Auto-aprovação configurável (conservador/recomendado/autônomo)
  - [ ] Dialog de confirmação ao ativar/pausar triagem
  - [ ] 3 indicadores de progresso corretos

Arquivos de Referencia (Prototipo Replit):
  - ScreeningConfigManager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx

Nota MVP (v1):
  - MVP v1: Todas as configurações editáveis no MVP
  - Pós-MVP: Configurações avançadas por canal, A/B testing de presets

Integracoes e Impactos:
  Componentes Afetados:
    - Preview da Vaga (CFG-001) — seções de Agendamento e Canais refletem config
  Vinculacoes:
    - CFG-006, CFG-007 — descrição e perguntas são os outros 2 indicadores de progresso
    - CFG-012 — indicadores de progresso vinculados a configDone/jdDone/questionsDone
  Comportamentos Automaticos:
    - Ativar triagem atualiza screeningStatus para 'active'
    - Pausar triagem atualiza screeningStatus para 'paused'

Dados e Estado:
  Interfaces:
    - "ScreeningConfig { channels, settings, scheduling }"
  Campos:
    - whatsapp, chat_web, phone (toggles)
    - minScorePreset (select), timeoutHours (number), maxRetries (number)
    - scheduling.enabled (toggle), calendarProvider (select), availableHours (text), interviewDuration (number)
    - autoApprovalPreset (select)
  Estados do Componente:
    - isEditingScreeningConfig: boolean
    - editChannels, editMinScorePreset, editTimeoutHours, editMaxRetries, etc.
    - showScreeningToggleConfirm: 'activate' | 'pause' | null

QA/Teste:
  Cenarios de Teste:
    - "Alternar canais e salvar"
    - "Selecionar preset de score e verificar valor mínimo"
    - "Configurar agendamento completo"
    - "Ativar triagem com dialog de confirmação"
    - "Pausar triagem com dialog de confirmação"
    - "Verificar indicadores de progresso"
  Casos Edge:
    - "Desativar todos os canais — erro inline"
    - "Timeout = 0 — erro inline"
    - "Retentativas = 6 — erro inline"
    - "Cancelar edição restaura valores originais"
  Checklist de Regressao:
    - [ ] Preview reflete configurações salvas
    - [ ] Indicadores de progresso atualizam
    - [ ] Status de triagem (CFG-011) reflete ativação/pausa

Bitbucket Commit:
  Branch: feature/CFG-005-screening-config
  Commit Pattern: "[CFG-005] feat: implementar configurações do roteiro de triagem"
  PR Checklist:
    - [ ] Toggles de canais
    - [ ] Presets de score e auto-aprovação
    - [ ] Agendamento
    - [ ] Dialog de confirmação
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar sub-seção "Configurações do Roteiro" na configuração de triagem da vaga.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência: plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx (linhas 60-98, 419-433)

    Configurações:
    - Canais: whatsapp (on), chat_web (on), phone (off) — v-switch
    - Score: rigoroso/recomendado/flexível — v-btn-toggle
    - Timeout: 48h default (v-text-field number, 1-168)
    - Retentativas: 2 default (v-text-field number, 0-5)
    - Agendamento: enabled toggle, minScorePreset, calendarProvider (Microsoft), availableHours (9h-18h), interviewDuration (60min)
    - Auto-aprovação: conservador/recomendado/autônomo — v-btn-toggle
    - Dialog confirmação ativar/pausar triagem
    - 3 indicadores: configDone, jdDone, questionsDone

    API: PUT /api/v1/jobs/:id/screening-config
```

---

### CFG-006: Tab Configurações da Vaga — Descrição do Cargo para Triagem

```yaml
Titulo: "[FULL-STACK] Tab Configurações da Vaga — Descrição do Cargo para Triagem"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 5
Prioridade: Alta
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-005

Descricao: |
  Sub-seção "Descrição do Cargo" que fornece contexto de JD (Job Description) para a LIA usar na triagem.
  Inclui o texto da descrição de cargo, painel de avaliação WSI do JD com score,
  layout em 2 colunas com sugestões de competências geradas por IA,
  e geração assistida de JD por IA.

Historia de Usuario: |
  Como recrutador, eu quero fornecer e validar a descrição do cargo
  para que a LIA tenha contexto adequado ao conduzir a triagem WSI com os candidatos.

Regras de Negocio:
  1. JD text é o texto usado pela LIA como contexto de triagem
  2. Painel de avaliação WSI analisa qualidade do JD e exibe score
  3. Sugestões de competências são geradas por IA a partir do JD
  4. Geração de JD por IA usa dados da vaga como input
  5. JD preenchido marca indicador jdDone como true no progresso
  6. Read/Edit modes como nas demais seções

Requisitos Tecnicos:
  Frontend:
    - v-textarea para JD text com auto-resize
    - JDEvaluationPanel component para exibir score WSI
    - Layout 2 colunas: JD à esquerda, sugestões IA à direita
    - Botão "Gerar JD com IA" que chama endpoint
    - Lista de competências sugeridas com botão aceitar/rejeitar
  Backend:
    - POST /api/backend-proxy/jd/generate — gerar JD via IA
    - POST /api/backend-proxy/wsi/jd-evaluate — avaliar qualidade do JD
    - PUT /api/v1/jobs/:id — salvar description atualizada
  Dados:
    - "JDEvaluation { score: number, feedback: string[], suggestions: string[] }"
    - description: string (campo da vaga)
  Validacoes:
    - JD text mínimo 100 caracteres para avaliação WSI
    - JD text máximo 10.000 caracteres

Design & Componentes:
  Componentes Existentes:
    - v-textarea, v-btn, v-card (Vuetify 3)
  Novos Componentes:
    - JDScreeningSection.vue — seção completa
    - JDEvaluationPanel.vue — painel de score WSI (convertido de React)
    - AICompetencySuggestions.vue — lista de sugestões com aceitar/rejeitar
  Design Tokens:
    - score-high: text-green-600 bg-green-50
    - score-medium: text-amber-600 bg-amber-50
    - score-low: text-red-600 bg-red-50
    - ai-suggestion: bg-blue-50 border-blue-200
  Layout:
    - 2 colunas: JD textarea (60%) + painel avaliação/sugestões (40%)
    - Painel de avaliação acima das sugestões na coluna direita
  Estados:
    - Read mode, Edit mode
    - Avaliando JD (loading com spinner)
    - Gerando JD por IA (loading com progress)
    - JD avaliado com score
  Acessibilidade:
    - Textarea com aria-label "Descrição do cargo para triagem"
    - Score com aria-live para atualização automática
    - Sugestões navegáveis por teclado

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona "Descrição do Cargo" na sidebar
    2. JD atual exibido (ou vazio)
    3. Recrutador edita JD ou clica "Gerar com IA"
    4. Sistema avalia JD e mostra score WSI
    5. Sugestões de competências aparecem na coluna direita
    6. Recrutador aceita/rejeita sugestões
    7. Recrutador salva
  Estados de Botoes:
    - "Gerar JD com IA" — visível em edit mode, loading durante geração
    - "Avaliar JD" — avalia qualidade do texto atual
    - Sugestões: "Aceitar" / "Rejeitar" por item
  Validacoes Inline:
    - JD < 100 chars — mensagem "Descrição muito curta para avaliação"
  Mensagens de Feedback:
    - Toast "Descrição do cargo salva com sucesso"
    - "Avaliando qualidade do JD..." durante loading
    - Score badge com valor numérico

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] JD textarea com auto-resize
  - [ ] Painel de avaliação WSI com score
  - [ ] Layout 2 colunas
  - [ ] Geração de JD por IA
  - [ ] Sugestões de competências
  - [ ] API integrada
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] JD editável em textarea
  - [ ] Botão "Gerar JD com IA" gera descrição a partir dos dados da vaga
  - [ ] Painel WSI exibe score numérico com cor semântica
  - [ ] Sugestões de competências exibidas na coluna direita
  - [ ] Aceitar sugestão adiciona competência ao JD
  - [ ] JD preenchido ativa indicador jdDone

Arquivos de Referencia (Prototipo Replit):
  - ScreeningConfigManager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx

Nota MVP (v1):
  - MVP v1: JD editável + avaliação WSI + geração IA
  - Pós-MVP: Sugestões avançadas com fine-tuning por indústria

Integracoes e Impactos:
  Componentes Afetados:
    - Preview da Vaga (CFG-001) — descrição exibida no preview
  Vinculacoes:
    - CFG-005 — jdDone é um dos 3 indicadores de progresso
    - CFG-007 — JD é contexto para geração de perguntas WSI
  Comportamentos Automaticos:
    - JD preenchido atualiza indicador jdDone automaticamente

Dados e Estado:
  Interfaces:
    - "JDEvaluation { score: number, feedback: string[], suggestions: string[] }"
  Campos:
    - description (textarea)
  Estados do Componente:
    - isEditingJD: boolean
    - jdEvaluation: JDEvaluation | null
    - isEvaluating: boolean
    - isGenerating: boolean

QA/Teste:
  Cenarios de Teste:
    - "Editar JD e salvar"
    - "Gerar JD por IA com dados da vaga preenchidos"
    - "Avaliar JD e receber score"
    - "Aceitar sugestão de competência"
    - "JD vazio — indicador jdDone false"
  Casos Edge:
    - "JD < 100 caracteres — avaliação mostra alerta"
    - "JD > 10.000 caracteres — truncar ou alertar"
    - "Geração IA com vaga sem dados — mensagem de erro"
    - "Network error durante avaliação — toast de erro"
  Checklist de Regressao:
    - [ ] Preview (CFG-001) reflete JD atualizado
    - [ ] Indicador jdDone atualiza corretamente
    - [ ] Geração de perguntas WSI (CFG-007) usa JD atualizado

Bitbucket Commit:
  Branch: feature/CFG-006-jd-triagem
  Commit Pattern: "[CFG-006] feat: implementar descrição do cargo para triagem"
  PR Checklist:
    - [ ] JD textarea
    - [ ] Painel WSI
    - [ ] Geração IA
    - [ ] Sugestões
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar sub-seção "Descrição do Cargo" para fornecer contexto de JD à LIA.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência: plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx

    Implementar:
    - v-textarea para JD com auto-resize
    - JDEvaluationPanel: score WSI com cor semântica (verde >80, âmbar 50-80, vermelho <50)
    - Layout 2 colunas (JD 60% + avaliação/sugestões 40%)
    - Botão "Gerar JD com IA": POST /api/backend-proxy/jd/generate
    - Botão "Avaliar JD": POST /api/backend-proxy/wsi/jd-evaluate
    - Sugestões de competências com aceitar/rejeitar
    - JD preenchido (trim().length > 0) marca jdDone = true
```

---

### CFG-007: Tab Configurações da Vaga — Perguntas de Triagem (Blocos WSI)

```yaml
Titulo: "[FULL-STACK] Tab Configurações da Vaga — Perguntas de Triagem (Blocos WSI)"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 8
Prioridade: Crítica
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-005, CFG-006, CFG-009

Descricao: |
  Sub-seção "Perguntas de Triagem" com a estrutura completa WSI (WeDo Screening Interview).
  ESTE É O MAIOR CARD DO ÉPICO.

  7 blocos WSI, expandíveis/colapsáveis via expandedBlocks state.

  O Bloco 2 integra 3 camadas de perguntas:

  1. Perguntas Derivadas (DerivedQuestions):
     - Auto-geradas a partir dos campos da vaga via 5 perguntas padrão do sistema
     - workModel → {modeloTrabalho}, type → {tipoContratação}, location → {localização}, languages → {idioma}/{nível}, isAffirmative
     - Interface: DerivedQuestion {id, sourceField, sourceLabel, question, character, enabled, expectedAnswer, context, systemQuestionId}
     - Toggle enable/disable por pergunta
     - resolveTemplate() substitui placeholders
     - generateDerivedQuestions(job) function

  2. Perguntas do Banco da Empresa (CompanyBankQuestions):
     - Do banco central (eligibility-questions-bank.ts), excluindo system defaults
     - Agrupadas por QUESTION_CATEGORIES (9 categorias)
     - Seletor por categoria com botões + para adicionar
     - Mostra detalhes completos (expectedAnswer, contextHint)
     - bankQuestionOverrides state para overrides de character/expectedAnswer

  3. Perguntas Personalizadas (CustomQuestions):
     - Criadas pelo recrutador para esta vaga específica
     - Interface: CustomQuestion {id, question, character, expectedAnswer}
     - Add/remove/edit inline
     - Toggle eliminatória/classificatória

  Geração WSI: handleGenerateWSI com modos compact/full, animação de progresso 4 etapas,
  mensagens tipadas, chamada backend /api/backend-proxy/wsi/generate-batch, fallback mock templates.

  Por bloco: input de prompt para sugestão IA, feedback de geração.
  Edição de perguntas: edit inline, aceitar/desativar perguntas geradas.
  Modos Read/Edit para todos os blocos.

Historia de Usuario: |
  Como recrutador, eu quero configurar as perguntas de triagem WSI da vaga
  para que a LIA conduza entrevistas estruturadas e eficazes com os candidatos.

Regras de Negocio:
  1. 7 blocos WSI com perguntas organizadas por tipo (elegibilidade, técnica, comportamental, etc.)
  2. Bloco 2 combina 3 fontes: derivadas, banco empresa, personalizadas
  3. Perguntas derivadas são auto-geradas quando campos da vaga são preenchidos
  4. resolveTemplate() substitui {modeloTrabalho}, {tipoContratação}, {localização}, {idioma}, {nível}
  5. Toggle enable/disable preserva estado ao regenerar (merge via prevMap)
  6. Perguntas do banco excluem isSystemDefault === true
  7. Perguntas personalizadas podem ser eliminatórias ou classificatórias
  8. Geração WSI tem 2 modos: compact (menos perguntas) e full (mais perguntas)
  9. Geração tem animação 4 etapas: analisando JD, buscando critérios, aplicando framework CBI, finalizando
  10. Fallback para mock templates quando backend falha
  11. Perguntas geradas podem ser aceitas, editadas ou desativadas
  12. questionsDone = true quando há perguntas aceitas ou screeningQuestions.length > 0

Requisitos Tecnicos:
  Frontend:
    - 7 blocos WSI como v-expansion-panels
    - DerivedQuestions component com v-switch e badges
    - CompanyBankQuestions com accordion de categorias e botões +
    - CustomQuestions com inline edit e add/remove
    - Geração WSI com progress stepper animado e mensagens tipadas
    - Per-block: v-text-field para prompt IA + botão sugerir
    - Inline edit com v-text-field e botões confirmar/cancelar
  Backend:
    - POST /api/backend-proxy/wsi/generate-batch — gerar perguntas WSI
    - POST /api/backend-proxy/wsi/suggest-question — sugerir pergunta por bloco
    - PUT /api/v1/jobs/:id/screening-config — salvar perguntas
  Dados:
    - "DerivedQuestion { id, sourceField, sourceLabel, question, character, enabled, expectedAnswer?, context?, systemQuestionId? }"
    - "CustomQuestion { id, question, character, expectedAnswer? }"
    - "WSI_BLOCKS: array de 7 blocos com id, name, description, duration, editable, type"
    - "QUESTION_CATEGORIES: 9 categorias (general, eligibility, availability, education, experience, languages, compensation, work_model, compliance)"
  Validacoes:
    - Pergunta custom: question text obrigatório (min 10 chars)
    - Pelo menos 1 pergunta ativa para marcar questionsDone
    - Máximo 50 perguntas por vaga

Design & Componentes:
  Componentes Existentes:
    - v-expansion-panels, v-switch, v-chip, v-text-field, v-btn (Vuetify 3)
  Novos Componentes:
    - WSIBlocksSection.vue — seção principal com 7 blocos
    - DerivedQuestions.vue — camada de perguntas derivadas
    - CompanyBankQuestions.vue — camada de perguntas do banco
    - CustomQuestions.vue — camada de perguntas personalizadas
    - WSIGenerationProgress.vue — stepper animado com mensagens tipadas
    - QuestionInlineEdit.vue — edição inline de pergunta
    - BlockPromptInput.vue — input de prompt IA por bloco
  Design Tokens:
    - badge-eliminatoria: bg-red-50 text-red-700
    - badge-classificatoria: bg-amber-50 text-amber-700
    - derived-header: text-11px uppercase tracking-wider font-semibold
    - bank-category: expandable com ícone emoji
    - custom-add: border-dashed-2 border-gray-300
    - generation-step-active: bg-cyan-500 text-white
    - generation-step-done: bg-green-500 text-white
  Layout:
    - 7 blocos verticais expandíveis
    - Bloco 2 com 3 sub-seções (derivadas, banco, custom)
    - Cada pergunta em linha com toggle/texto/badge/ações
    - Geração WSI em overlay ou seção dedicada
  Estados:
    - Read mode — perguntas visíveis sem edição
    - Edit mode — todos os controles de edição visíveis
    - Generating — stepper animado com 4 etapas e mensagens tipadas
    - Generated — perguntas geradas visíveis com aceitar/rejeitar
    - Block expanded/collapsed via expandedBlocks
  Acessibilidade:
    - Expansion panels com aria-expanded
    - Toggles com labels descritivos
    - Progress stepper com aria-live
    - Inline edit com focus management

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona "Perguntas de Triagem" na sidebar
    2. 7 blocos WSI exibidos, expandidos/colapsados
    3. Bloco 2 mostra perguntas derivadas, banco e personalizadas
    4. Recrutador pode editar, adicionar ou gerar perguntas
    5. Para gerar: escolhe modo compact/full, aguarda geração com progresso visual
    6. Perguntas geradas aparecem nos blocos correspondentes
    7. Recrutador aceita, edita ou desativa perguntas geradas
    8. Recrutador salva configuração
  Estados de Botoes:
    - "Gerar WSI Compact" / "Gerar WSI Completo" — modos de geração
    - "Aceitar" / "Desativar" — por pergunta gerada
    - "+ Adicionar Pergunta" — personalizada (border dashed)
    - Toggles enable/disable — por pergunta derivada
    - "+ Adicionar" — por pergunta do banco (por categoria)
  Validacoes Inline:
    - Pergunta custom vazia — bloquear adição
    - Tentativa de salvar sem perguntas — alerta
  Mensagens de Feedback:
    - Progresso de geração: "Analisando job description...", "Buscando critérios de avaliação...", "Aplicando framework CBI...", "Finalizando roteiro de triagem..."
    - Toast "Perguntas de triagem salvas com sucesso"
    - Contagem de perguntas geradas no sumário

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] 7 blocos WSI expandíveis/colapsáveis
  - [ ] DerivedQuestions com auto-geração e toggles
  - [ ] CompanyBankQuestions com seletor por categoria
  - [ ] CustomQuestions com add/edit/remove
  - [ ] Geração WSI com 2 modos e progresso animado
  - [ ] Inline edit de perguntas geradas
  - [ ] Aceitar/desativar perguntas geradas
  - [ ] Input de prompt IA por bloco
  - [ ] API integrada (generate-batch, suggest-question)
  - [ ] Fallback mock templates
  - [ ] Testes unitários com cobertura > 80%
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] 7 blocos WSI renderizados com expand/collapse
  - [ ] Perguntas derivadas auto-geradas ao preencher campos da vaga
  - [ ] Toggles de enable/disable funcionam para perguntas derivadas
  - [ ] Banco da empresa mostra perguntas agrupadas por 9 categorias
  - [ ] Botão + adiciona pergunta do banco à vaga
  - [ ] Perguntas personalizadas podem ser criadas com eliminatória/classificatória
  - [ ] Geração WSI compact gera menos perguntas que full
  - [ ] Progresso de geração mostra 4 etapas com mensagens animadas
  - [ ] Perguntas geradas podem ser aceitas ou desativadas
  - [ ] questionsDone ativado quando há perguntas

Arquivos de Referencia (Prototipo Replit):
  - ScreeningConfigManager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx
  - DerivedQuestions.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/DerivedQuestions.tsx
  - CompanyBankQuestions.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/CompanyBankQuestions.tsx
  - CustomQuestions.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/CustomQuestions.tsx

Nota MVP (v1):
  - MVP v1: Blocos WSI + 3 camadas de perguntas + geração IA + inline edit
  - Pós-MVP: IA avançada com fine-tuning por empresa, templates de roteiro

Integracoes e Impactos:
  Componentes Afetados:
    - Preview da Vaga (CFG-001) — contagem de perguntas e tempo estimado
  Vinculacoes:
    - CFG-005 — questionsDone é indicador de progresso
    - CFG-006 — JD é contexto para geração de perguntas
    - CFG-009 — banco central é fonte para CompanyBankQuestions
    - CFG-012 — campos da vaga geram perguntas derivadas automaticamente
  Comportamentos Automaticos:
    - Alterar campos da vaga (workModel, type, location, languages, isAffirmative) regenera perguntas derivadas
    - Merge preserva toggle state via prevMap ao regenerar

Dados e Estado:
  Interfaces:
    - "DerivedQuestion { id, sourceField, sourceLabel, question, character, enabled, expectedAnswer?, context?, systemQuestionId? }"
    - "CustomQuestion { id, question, character, expectedAnswer? }"
    - "BankQuestion { id, question, character, expectedAnswer?, contextHint? }"
  Campos:
    - derivedQuestions (DerivedQuestion[])
    - selectedBankQuestions (string[])
    - bankQuestionOverrides (Record<string, {character?, expectedAnswer?}>)
    - customQuestions (CustomQuestion[])
    - generatedQuestions (Record<number, any[]>)
    - acceptedQuestions (Set<string>)
    - deactivatedQuestions (Set<string>)
    - expandedBlocks (number[])
  Estados do Componente:
    - isEditingScreening, isGeneratingWSI, wsiGenerationMode, wsiGenerationStep (0-4)
    - wsiDynamicMessage, wsiTypedMessage, wsiGenerationCompleted
    - blockPromptOpen, blockPromptText, isSuggestingQuestion

QA/Teste:
  Cenarios de Teste:
    - "Preencher workModel na vaga — pergunta derivada gerada automaticamente"
    - "Toggle enable/disable em pergunta derivada"
    - "Adicionar pergunta do banco por categoria"
    - "Criar pergunta personalizada eliminatória com resposta esperada"
    - "Gerar WSI modo compact — verificar perguntas geradas"
    - "Gerar WSI modo full — verificar mais perguntas"
    - "Aceitar e desativar perguntas geradas"
    - "Editar pergunta inline"
    - "Input de prompt IA por bloco"
    - "Fallback mock quando backend falha"
  Casos Edge:
    - "Alterar campo da vaga após gerar perguntas — merge preserva toggles"
    - "Banco sem perguntas disponíveis — mensagem 'Todas já selecionadas'"
    - "50 perguntas (máximo) — bloquear adição"
    - "Geração com vaga sem JD — alerta 'Preencha a descrição primeiro'"
    - "Network error durante geração — fallback mock templates"
    - "Desativar todas as perguntas — questionsDone false"
  Checklist de Regressao:
    - [ ] Perguntas derivadas regeneram ao alterar campos da vaga
    - [ ] Banco reflete alterações do CFG-009
    - [ ] Preview (CFG-001) atualiza contagem de perguntas
    - [ ] Indicador questionsDone atualiza corretamente

Bitbucket Commit:
  Branch: feature/CFG-007-perguntas-triagem-wsi
  Commit Pattern: "[CFG-007] feat: implementar perguntas de triagem com blocos WSI"
  PR Checklist:
    - [ ] 7 blocos WSI
    - [ ] 3 camadas de perguntas (derivadas, banco, custom)
    - [ ] Geração WSI com progresso
    - [ ] Inline edit
    - [ ] Fallback mock
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar sub-seção "Perguntas de Triagem" com estrutura completa WSI.
    ESTE É O MAIOR COMPONENTE — inclui 7 blocos WSI com 3 camadas de perguntas no Bloco 2.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referências do protótipo Replit:
    - ScreeningConfigManager.tsx (geração WSI, blocos, progresso)
    - DerivedQuestions.tsx (perguntas derivadas, resolveTemplate, generateDerivedQuestions)
    - CompanyBankQuestions.tsx (banco empresa, categorias, overrides)
    - CustomQuestions.tsx (personalizadas, add/edit/remove)

    Implementar:
    1. WSIBlocksSection.vue — 7 blocos v-expansion-panels
    2. DerivedQuestions.vue — perguntas auto-geradas de campos da vaga:
       - 5 system defaults: workModel→{modeloTrabalho}, type→{tipoContratação}, location→{localização}, languages→{idioma}/{nível}, isAffirmative
       - resolveTemplate() para placeholders
       - generateDerivedQuestions(job) function
       - Toggle enable/disable com merge via prevMap
    3. CompanyBankQuestions.vue — banco central (!isSystemDefault):
       - 9 categorias com accordion
       - Botão + por pergunta, X para remover selecionada
       - bankQuestionOverrides para character/expectedAnswer
    4. CustomQuestions.vue — perguntas criadas pelo recrutador:
       - Add/edit/remove inline
       - Toggle eliminatória/classificatória
    5. WSIGenerationProgress.vue — geração com 2 modos (compact/full):
       - 4 etapas: analisar JD, buscar critérios, aplicar CBI, finalizar
       - Mensagens tipadas animadas (25ms por char)
       - POST /api/backend-proxy/wsi/generate-batch
       - Fallback mock templates se backend falhar

    Badges: eliminatória (bg-red-50 text-red-700), classificatória (bg-amber-50 text-amber-700)
```

---

### CFG-008: Menu Configurações — Pipeline de Recrutamento

```yaml
Titulo: "[FULL-STACK] Menu Configurações — Pipeline de Recrutamento"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 5
Prioridade: Alta
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: Nenhuma

Descricao: |
  Tab "Pipeline" no menu Configurações da empresa.
  Componente visual RecruitmentJourneyConfig para gerenciar o pipeline de recrutamento padrão.
  CRUD completo de etapas: adicionar, editar, remover, reordenar.
  Drag-and-drop para ordenação, cores por etapa.
  Persistência via API REST (POST/PUT/DELETE) para templates de pipeline.
  Badge de status de sincronização (Sincronizado / Alterações não salvas).
  Modos Read/Edit com botões Editar/Salvar Alterações/Cancelar.
  Loading skeleton durante fetch e toast messages para feedback.
  Serve como template padrão para o Processo Seletivo das vagas (CFG-003).

Historia de Usuario: |
  Como administrador da empresa, eu quero configurar o pipeline de recrutamento padrão
  para que todas as novas vagas herdem as etapas padrão automaticamente.

Regras de Negocio:
  1. Pipeline serve como template default para novas vagas (CFG-003)
  2. CRUD completo: adicionar, editar nome, remover, reordenar etapas
  3. Cores configuráveis por etapa
  4. Drag-and-drop para reordenação
  5. Badge "Sincronizado" quando salvo, "Alterações não salvas" quando modificado
  6. Ao criar template, é marcado como is_default
  7. Deletar template requer confirmação via dialog
  8. Ao deletar, pipeline reseta para DEFAULT_STAGES
  9. Loading skeleton durante carregamento inicial

Requisitos Tecnicos:
  Frontend:
    - RecruitmentJourneyConfig component convertido para Vue 3
    - Drag-and-drop com vuedraggable ou Sortable.js
    - v-color-picker para cores por etapa
    - Badge de sincronização com v-chip
    - Loading skeleton com v-skeleton-loader
    - Dialog de confirmação para delete com v-dialog
  Backend:
    - GET /api/backend-proxy/recruitment-journey/templates?company_id=X — listar templates
    - POST /api/backend-proxy/recruitment-journey/templates — criar template
    - PUT /api/backend-proxy/recruitment-journey/templates?template_id=X — atualizar
    - DELETE /api/backend-proxy/recruitment-journey/templates?template_id=X — deletar
  Dados:
    - "RecruitmentStage { id: string, name: string, displayName: string, color?: string, order: number, isActive: boolean, stageCategory: string, isEditable?: boolean, isRemovable?: boolean, isReorderable?: boolean, liaAssisted?: boolean, defaultSlaDays?: number }"
    - DEFAULT_STAGES: array padrão de etapas
  Validacoes:
    - Nome de etapa obrigatório
    - Máximo 20 etapas
    - Nome de etapa único (case-insensitive)

Design & Componentes:
  Componentes Existentes:
    - v-card, v-btn, v-chip, v-dialog, v-skeleton-loader (Vuetify 3)
  Novos Componentes:
    - PipelineTab.vue — tab principal
    - RecruitmentJourneyConfig.vue — componente visual do pipeline
    - PipelineStageCard.vue — card de etapa com drag handle e controles
    - DeleteTemplateDialog.vue — dialog de confirmação
  Design Tokens:
    - sync-badge: bg-green-50 text-green-600 border-green-200 (Sincronizado)
    - unsaved-badge: bg-gray-100 text-gray-700 border-gray-200 (Alterações não salvas)
    - stage-card: rounded-xl, border, hover effect
  Layout:
    - Pipeline visual horizontal ou vertical com cards de etapa
    - Header com badges de status e botões de ação
    - Dialog de confirmação centralizado
  Estados:
    - Loading — skeleton loader
    - Read mode — pipeline visual sem edição
    - Edit mode — drag handles, botões edit/remove visíveis
    - Saving — botão "Salvando..." com loader
    - Deleting — dialog de confirmação
    - Synced — badge verde "Sincronizado"
    - Unsaved — badge cinza "Alterações não salvas"
  Acessibilidade:
    - Drag-and-drop com alternativa de teclado (botões up/down)
    - Dialog com focus trapping
    - Status badges com aria-label

Comportamento de UI:
  Fluxo Principal:
    1. Admin acessa tab "Pipeline" nas Configurações
    2. Pipeline atual exibido (do backend ou DEFAULT_STAGES)
    3. Admin clica "Editar"
    4. Admin pode adicionar, renomear, remover, reordenar etapas
    5. Badge mostra "Alterações não salvas"
    6. Admin clica "Salvar Alterações"
    7. Badge mostra "Sincronizado"
  Estados de Botoes:
    - "Editar" — read mode
    - "Salvar Alterações" — edit mode, habilitado apenas com alterações
    - "Cancelar" — restaura estado anterior
    - "Deletar Template" — read mode, com confirmação
  Validacoes Inline:
    - Nome vazio ao salvar — destaque vermelho
  Mensagens de Feedback:
    - Toast "Pipeline salvo com sucesso!"
    - Toast "Erro ao salvar pipeline. Tente novamente."
    - Toast "Template deletado. Pipeline resetado para padrão."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Pipeline visual renderizado
  - [ ] CRUD de etapas funcionando
  - [ ] Drag-and-drop para reordenação
  - [ ] Cores por etapa
  - [ ] Badge de sincronização
  - [ ] API integrada (GET/POST/PUT/DELETE)
  - [ ] Dialog de confirmação para delete
  - [ ] Loading skeleton
  - [ ] Toast messages
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] Pipeline exibido com etapas ordenadas
  - [ ] Etapas podem ser adicionadas, renomeadas, removidas e reordenadas
  - [ ] Drag-and-drop funciona para reordenação
  - [ ] Cores configuráveis por etapa
  - [ ] Badge "Sincronizado" após salvar, "Alterações não salvas" após modificar
  - [ ] Deletar template exige confirmação e reseta para padrão
  - [ ] Skeleton loader durante carregamento
  - [ ] Toast de sucesso/erro após operações

Arquivos de Referencia (Prototipo Replit):
  - RecruitmentHub.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/settings/RecruitmentHub.tsx

Nota MVP (v1):
  - MVP v1: CRUD completo + sincronização + delete com confirmação
  - Pós-MVP: Templates múltiplos, clone de pipeline, versionamento

Integracoes e Impactos:
  Componentes Afetados:
    - Processo Seletivo da Vaga (CFG-003) — herda pipeline como default
  Vinculacoes:
    - CFG-003 — getCompanyPipelineStages() usa pipeline da empresa como fallback
    - CFG-012 — mudanças no pipeline empresa podem impactar vagas existentes
  Comportamentos Automaticos:
    - Novas vagas sem etapas configuradas herdam pipeline da empresa automaticamente

Dados e Estado:
  Interfaces:
    - "RecruitmentStage { id, name, displayName, color, order, isActive, stageCategory, isEditable, isRemovable, isReorderable, liaAssisted, defaultSlaDays }"
  Campos:
    - recruitmentStages (RecruitmentStage[])
    - currentTemplateId (string | null)
    - companyId (string | null)
  Estados do Componente:
    - loading, saving, savingStages, deletingTemplate: boolean
    - hasStageChanges: boolean
    - isEditingPipeline: boolean
    - showDeleteConfirm: boolean
    - originalStages, stagesBeforeEdit: RecruitmentStage[]

QA/Teste:
  Cenarios de Teste:
    - "Carregar pipeline do backend"
    - "Adicionar nova etapa ao pipeline"
    - "Remover etapa do pipeline"
    - "Reordenar etapas via drag-and-drop"
    - "Salvar pipeline — badge muda para Sincronizado"
    - "Cancelar edição — restaurar estado anterior"
    - "Deletar template — confirmar e resetar para padrão"
    - "Loading skeleton durante fetch"
  Casos Edge:
    - "Backend indisponível — mostrar erro"
    - "Salvar pipeline vazio — bloquear"
    - "20 etapas (máximo) — bloquear adição"
    - "Template já deletado — tratar gracefully"
  Checklist de Regressao:
    - [ ] Vagas novas herdam pipeline atualizado
    - [ ] CFG-003 usa getCompanyPipelineStages() corretamente
    - [ ] DELETE funciona mesmo com multiple reloads

Bitbucket Commit:
  Branch: feature/CFG-008-pipeline-recrutamento
  Commit Pattern: "[CFG-008] feat: implementar pipeline de recrutamento nas configurações"
  PR Checklist:
    - [ ] CRUD de etapas
    - [ ] Drag-and-drop
    - [ ] API REST integrada
    - [ ] Badge de sincronização
    - [ ] Dialog de delete
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar tab "Pipeline" no menu Configurações da empresa.
    Pipeline visual de recrutamento com CRUD de etapas e sincronização com backend.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência: plataforma-lia/src/components/settings/RecruitmentHub.tsx (linhas 259-676)

    Implementar:
    - RecruitmentJourneyConfig: pipeline visual com etapas arrastáveis
    - CRUD: adicionar (nome + cor), editar nome, remover, reordenar (drag-and-drop com vuedraggable)
    - API REST:
      GET /api/backend-proxy/recruitment-journey/templates?company_id=X
      POST /api/backend-proxy/recruitment-journey/templates (criar)
      PUT /api/backend-proxy/recruitment-journey/templates?template_id=X (atualizar)
      DELETE /api/backend-proxy/recruitment-journey/templates?template_id=X (deletar)
    - Badge sincronização: v-chip verde "Sincronizado" / cinza "Alterações não salvas"
    - Botões: Editar / Salvar Alterações / Cancelar / Deletar Template
    - Dialog confirmação delete: "Tem certeza? Pipeline resetará para padrão"
    - Loading: v-skeleton-loader durante fetch
    - Toast: sucesso/erro via sonner ou v-snackbar
    - DEFAULT_STAGES como fallback
```

---

### CFG-009: Menu Configurações — Perguntas de Elegibilidade (Banco Central)

```yaml
Titulo: "[FULL-STACK] Menu Configurações — Perguntas de Elegibilidade (Banco Central)"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 8
Prioridade: Alta
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: Nenhuma

Descricao: |
  Tab "Perguntas de Elegibilidade" no menu Configurações. Dividida em DUAS seções:

  Seção 1 - Perguntas Padrão do Sistema (5 perguntas vinculadas a campos da vaga):
  - sys-workmodel: "Você tem disponibilidade para trabalhar no modelo {modeloTrabalho}?" (yesno, eliminatória, resposta: Sim, linkedField: workModel)
  - sys-contract-type: "Você aceita contratação no regime {tipoContratação}?" (yesno, eliminatória, resposta: Sim, linkedField: type)
  - sys-location: "Você reside ou tem disponibilidade para trabalhar em {localização}?" (yesno, classificatória, linkedField: location)
  - sys-language: "Qual seu nível de proficiência em {idioma}? (Mínimo: {nível})" (text, eliminatória, linkedField: languages)
  - sys-affirmative: "Você se enquadra nos critérios afirmativos desta vaga?" (yesno, classificatória, linkedField: isAffirmative)

  Cada pergunta mostra: badge de campo vinculado (azul), badge eliminatória (vermelho) com resposta esperada OU badge classificatória (âmbar).
  Modo edição: editar texto, toggle eliminatória, set resposta esperada (Sim/Não radio para tipo yesno).

  Seção 2 - Perguntas de Elegibilidade (perguntas da empresa):
  - 6 perguntas padrão obrigatórias (isDefault: true, required: true)
  - Cada pergunta: badge número, texto, badge tipo (Texto/Sim-Não/Escala), badge "Obrigatória", label "Padrão", badge eliminatória se aplicável
  - Modo edição: botão "Banco de Perguntas" (abre seletor com categorias), botão "Nova Pergunta" (abre formulário), delete de não-padrão, toggle required
  - Seletor de banco: categorias expandíveis, checkbox selection, indicador "Já adicionada", botão add em batch
  - Formulário nova pergunta: texto, tipo dropdown (Texto livre/Sim-Não/Escala 1-5), checkbox Obrigatória, checkbox Eliminatória, resposta esperada (Sim/Não radio quando eliminatória + yesno)

Historia de Usuario: |
  Como administrador da empresa, eu quero gerenciar as perguntas de elegibilidade centrais
  para padronizar as perguntas de triagem usadas em todas as vagas da empresa.

Regras de Negocio:
  1. 5 perguntas do sistema são vinculadas a campos da vaga e usam placeholders
  2. Perguntas do sistema alimentam DerivedQuestions (CFG-007) automaticamente
  3. Perguntas da empresa (não-sistema) alimentam CompanyBankQuestions (CFG-007)
  4. 6 perguntas padrão da empresa não podem ser deletadas (isDefault: true)
  5. linkedFieldLabels: workModel→"Modelo de Trabalho", type→"Tipo de Contratação", location→"Localização", languages→"Idiomas", isAffirmative→"Ações Afirmativas"
  6. Banco de perguntas organizado por 9 categorias (QUESTION_CATEGORIES)
  7. Indicador "Já adicionada" no seletor de banco evita duplicatas
  8. Novas perguntas podem ser eliminatórias ou classificatórias
  9. Perguntas eliminatórias yesno requerem resposta esperada (Sim ou Não)

Requisitos Tecnicos:
  Frontend:
    - Seção 1: lista de 5 perguntas sistema com badges de linkedField e character
    - Seção 2: lista de perguntas empresa com badges de tipo e status
    - Seletor de banco: accordion por categoria com checkboxes
    - Formulário nova pergunta: v-text-field, v-select, v-checkbox, v-radio-group
    - Edit mode para ambas as seções
  Backend:
    - GET /api/backend-proxy/screening-questions — listar perguntas
    - PUT /api/backend-proxy/screening-questions — salvar perguntas
    - eligibility-questions-bank.ts como source of truth para banco
  Dados:
    - "EligibilityQuestionTemplate { id, question, type, category, contextHint, options?, triggerCondition?, linkedField?, isSystemDefault?, eliminatory?, eliminatoryAnswer? }"
    - "ScreeningQuestion { id, question, type, required, order, isDefault, options?, is_eliminatory?, expected_answer? }"
    - "QUESTION_CATEGORIES: 9 categorias com label, icon, color"
    - "linkedFieldLabels: Record<string, string>"
  Validacoes:
    - Texto de pergunta obrigatório (min 10 caracteres)
    - Resposta esperada obrigatória para eliminatórias yesno
    - Perguntas padrão não podem ser deletadas

Design & Componentes:
  Componentes Existentes:
    - v-list, v-chip, v-checkbox, v-radio-group, v-text-field, v-select (Vuetify 3)
  Novos Componentes:
    - EligibilityQuestionsTab.vue — tab principal
    - SystemQuestionsSection.vue — seção 1 (perguntas do sistema)
    - CompanyQuestionsSection.vue — seção 2 (perguntas da empresa)
    - QuestionBankSelector.vue — seletor de banco com categorias
    - NewQuestionForm.vue — formulário de nova pergunta
  Design Tokens:
    - linkedField-badge: bg-blue-100 text-blue-700
    - eliminatoria-badge: bg-red-50 text-red-700
    - classificatoria-badge: bg-amber-50 text-amber-700
    - type-badge: bg-gray-100 text-gray-700
    - obrigatoria-badge: bg-blue-50 text-blue-700
    - padrao-label: text-gray-400 italic
    - number-badge: bg-gray-200 text-gray-800 rounded-full
  Layout:
    - Seção 1 no topo com header "Perguntas Padrão do Sistema"
    - Seção 2 abaixo com header "Perguntas de Elegibilidade"
    - Cada pergunta em card com badges alinhados à direita
    - Seletor de banco em modal ou panel expandível
  Estados:
    - Read mode — perguntas listadas sem edição
    - Edit mode sistema — editar texto, toggle eliminatória, set resposta
    - Edit mode empresa — adicionar/remover perguntas, toggle required
    - Bank selector open — accordion de categorias com checkboxes
    - New question form open — formulário inline
  Acessibilidade:
    - Checkboxes com labels descritivos
    - Radio groups com fieldset e legend
    - Accordion com aria-expanded
    - Badges com aria-label

Comportamento de UI:
  Fluxo Principal:
    1. Admin acessa tab "Perguntas de Elegibilidade"
    2. Seção 1 mostra 5 perguntas do sistema com badges
    3. Seção 2 mostra perguntas da empresa (6 padrão + adicionadas)
    4. Admin pode editar ambas as seções
    5. Seção 2: pode abrir banco de perguntas para adicionar em batch
    6. Seção 2: pode criar nova pergunta via formulário
    7. Admin salva alterações
  Estados de Botoes:
    - "Editar" — por seção, habilita modo edição
    - "Banco de Perguntas" — abre seletor com categorias
    - "Nova Pergunta" — abre formulário inline
    - "Adicionar X perguntas" — batch add do seletor de banco
    - "Salvar" / "Cancelar" — por seção
  Validacoes Inline:
    - Pergunta vazia — erro "Texto da pergunta é obrigatório"
    - Eliminatória yesno sem resposta — erro "Defina a resposta esperada"
  Mensagens de Feedback:
    - Toast "Perguntas padrão do sistema salvas com sucesso!"
    - Toast "Perguntas salvas com sucesso!"
    - Indicador "Já adicionada" no seletor de banco

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Seção 1 com 5 perguntas do sistema editáveis
  - [ ] Seção 2 com perguntas da empresa e 6 padrão
  - [ ] Seletor de banco com 9 categorias
  - [ ] Formulário de nova pergunta
  - [ ] Badges de linkedField, character, tipo, obrigatória
  - [ ] Edit mode para ambas as seções
  - [ ] API integrada
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] 5 perguntas do sistema exibidas com badges de campo vinculado
  - [ ] Editar texto de pergunta sistema funciona
  - [ ] Toggle eliminatória/classificatória funciona para perguntas sistema
  - [ ] Resposta esperada (Sim/Não radio) funciona para eliminatórias yesno
  - [ ] 6 perguntas padrão da empresa exibidas com badge "Padrão"
  - [ ] Perguntas padrão não podem ser deletadas
  - [ ] Seletor de banco mostra 9 categorias com accordion
  - [ ] Indicador "Já adicionada" aparece para perguntas já no banco
  - [ ] Nova pergunta pode ser criada com tipo, obrigatória, eliminatória
  - [ ] Batch add funciona do seletor de banco

Arquivos de Referencia (Prototipo Replit):
  - RecruitmentHub.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/settings/RecruitmentHub.tsx
  - eligibility-questions-bank.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/settings/eligibility-questions-bank.ts

Nota MVP (v1):
  - MVP v1: Ambas as seções editáveis, banco com 9 categorias, formulário nova pergunta
  - Pós-MVP: Perguntas condicionais por trigger, analytics de perguntas

Integracoes e Impactos:
  Componentes Afetados:
    - DerivedQuestions (CFG-007) — perguntas sistema alimentam perguntas derivadas
    - CompanyBankQuestions (CFG-007) — perguntas não-sistema alimentam banco na vaga
  Vinculacoes:
    - CFG-007 — ELIGIBILITY_QUESTIONS_BANK é single source of truth
    - CFG-012 — sistema defaults geram DerivedQuestions, não-defaults geram CompanyBankQuestions
  Comportamentos Automaticos:
    - Alterações nas perguntas do sistema refletem na geração de DerivedQuestions em todas as vagas

Dados e Estado:
  Interfaces:
    - "EligibilityQuestionTemplate { id, question, type, category, contextHint, options?, triggerCondition?, linkedField?, isSystemDefault?, eliminatory?, eliminatoryAnswer? }"
    - "ScreeningQuestion { id, question, type, required, order, isDefault, is_eliminatory?, expected_answer? }"
  Campos:
    - systemQuestions (EligibilityQuestionTemplate[]) — 5 perguntas do sistema
    - questions (ScreeningQuestion[]) — perguntas da empresa
  Estados do Componente:
    - isEditingSystemQuestions, isEditingQuestions: boolean
    - showQuestionBank, showQuestionForm: boolean
    - selectedBankQuestions: Set<string>
    - expandedCategories: Set<QuestionCategory>
    - newQuestion: { question, type, required, is_eliminatory, expected_answer }

QA/Teste:
  Cenarios de Teste:
    - "Editar texto de pergunta do sistema"
    - "Toggle eliminatória para pergunta do sistema"
    - "Set resposta esperada Sim/Não para eliminatória yesno"
    - "Adicionar pergunta do banco por categoria"
    - "Criar nova pergunta via formulário"
    - "Tentar deletar pergunta padrão — bloqueado"
    - "Deletar pergunta não-padrão"
    - "Batch add do seletor de banco"
    - "Indicador 'Já adicionada' funciona"
  Casos Edge:
    - "Todas as perguntas do banco já adicionadas — mensagem vazia"
    - "Eliminatória yesno sem resposta — erro ao salvar"
    - "Pergunta com texto < 10 chars — erro"
    - "Cancelar edição restaura estado anterior"
  Checklist de Regressao:
    - [ ] CFG-007 reflete alterações nas perguntas
    - [ ] DerivedQuestions usa system defaults atualizados
    - [ ] CompanyBankQuestions exclui system defaults

Bitbucket Commit:
  Branch: feature/CFG-009-perguntas-elegibilidade
  Commit Pattern: "[CFG-009] feat: implementar banco central de perguntas de elegibilidade"
  PR Checklist:
    - [ ] 2 seções (sistema + empresa)
    - [ ] Seletor de banco com 9 categorias
    - [ ] Formulário nova pergunta
    - [ ] Badges corretos
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar tab "Perguntas de Elegibilidade" nas Configurações da empresa.
    Banco central de perguntas com 2 seções: sistema (5 perguntas) e empresa.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referências:
    - plataforma-lia/src/components/settings/RecruitmentHub.tsx (linhas 678-1169)
    - plataforma-lia/src/components/settings/eligibility-questions-bank.ts

    Seção 1 - Perguntas Padrão do Sistema (5):
    - sys-workmodel: yesno, eliminatória, Sim, linkedField: workModel
    - sys-contract-type: yesno, eliminatória, Sim, linkedField: type
    - sys-location: yesno, classificatória, linkedField: location
    - sys-language: text, eliminatória, linkedField: languages
    - sys-affirmative: yesno, classificatória, linkedField: isAffirmative
    - Badges: linkedField (azul), eliminatória (vermelho)/classificatória (âmbar)
    - Edit: editar texto, toggle eliminatória, Sim/Não radio para yesno

    Seção 2 - Perguntas da Empresa:
    - 6 padrão obrigatórias (isDefault: true)
    - Badges: número, tipo (Texto/Sim-Não/Escala), Obrigatória, Padrão, eliminatória
    - Edit: Banco de Perguntas (9 categorias accordion + checkboxes + batch add), Nova Pergunta (form com tipo/obrigatória/eliminatória/resposta)
    - linkedFieldLabels: { workModel: "Modelo de Trabalho", type: "Tipo de Contratação", location: "Localização", languages: "Idiomas", isAffirmative: "Ações Afirmativas" }
```

---

### CFG-010: Menu Configurações — Status de Candidatos, Solicitação de Dados e Instruções LIA

```yaml
Titulo: "[FULL-STACK] Menu Configurações — Status de Candidatos, Solicitação de Dados e Instruções LIA"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 5
Prioridade: Média
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: Nenhuma

Descricao: |
  Tabs restantes no menu Configurações da empresa:

  1. Status de Candidatos (CandidateStatusesTab):
     - Lista de possíveis status de candidatos no pipeline
     - CRUD de status

  2. Solicitação de Dados (DataRequestTab):
     - Configuração de dados solicitados aos candidatos
     - Usa companyId para vincular à empresa

  3. Instruções LIA:
     - Governança LIA (ShieldCheck icon): regras de governança (autoScheduleInterviews, autoSendNegativeFeedback, requiresValidationBeforeShortlist)
     - Salvar via POST /api/backend-proxy/company/governance-rules
     - LIA Field Definitions: toggle campos ativos/inativos
     - Salvar via POST /api/backend-proxy/company/culture-profile
     - Por campo: label, badge de categoria, descrição de localização, instruções customizadas (Bot icon)
     - LiaFieldToggle component: toggle + editor de instruções
     - Contagem de campos ativos/inativos, display agrupado
     - Loading state, mensagens de erro/sucesso

Historia de Usuario: |
  Como administrador da empresa, eu quero configurar status de candidatos, dados solicitados e instruções para a LIA
  para personalizar o comportamento do sistema de recrutamento.

Regras de Negocio:
  1. Status de candidatos são personalizáveis por empresa
  2. Dados solicitados definem campos obrigatórios para candidatos
  3. Governança LIA controla autonomia: agendamento automático, feedback negativo automático, validação antes de shortlist
  4. Campos LIA podem ser ativados/desativados individualmente
  5. Cada campo LIA pode ter instruções customizadas
  6. Campos agrupados por categoria (cultura, técnico, comportamental, etc.)

Requisitos Tecnicos:
  Frontend:
    - CandidateStatusesTab component convertido para Vue 3
    - DataRequestTab component convertido para Vue 3
    - Seção Governança LIA com 3 v-switch para regras
    - LiaFieldToggle com v-switch + v-textarea para instruções
    - Contadores de campos ativos/inativos
    - Loading state com v-skeleton-loader
  Backend:
    - GET/POST /api/backend-proxy/company/governance-rules
    - GET/POST /api/backend-proxy/company/culture-profile
    - Endpoints existentes para status e data requests
  Dados:
    - "GovernanceRules { autoScheduleInterviews: boolean, autoSendNegativeFeedback: boolean, requiresValidationBeforeShortlist: boolean }"
    - "LiaFieldDefinition { key: string, label: string, category: string, description: string, active: boolean, instructions?: string }"
  Validacoes:
    - Instruções LIA max 500 caracteres
    - Status de candidato: nome obrigatório, único

Design & Componentes:
  Componentes Existentes:
    - v-switch, v-textarea, v-chip, v-list (Vuetify 3)
  Novos Componentes:
    - CandidateStatusesTab.vue
    - DataRequestTab.vue
    - LiaInstructionsTab.vue
    - GovernanceRulesSection.vue
    - LiaFieldToggle.vue — toggle + editor de instruções
    - LiaFieldGroupDisplay.vue — campos agrupados por categoria
  Design Tokens:
    - governance-icon: ShieldCheck text-green-600
    - field-active: border-green-200 bg-green-50
    - field-inactive: border-gray-200 bg-gray-50
    - bot-icon: Bot text-cyan-500
  Layout:
    - Tabs horizontais: pipeline, screening, candidate-statuses, data-requests, lia-instructions
    - Conteúdo de cada tab renderizado condicionalmente
    - LIA instructions: seção governança no topo + campos abaixo
  Estados:
    - Loading, Read mode, Edit mode, Saving
    - Campos: active/inactive
    - showInactiveFields toggle
  Acessibilidade:
    - Toggles com labels descritivos
    - Textarea com aria-label
    - Contadores com aria-live

Comportamento de UI:
  Fluxo Principal:
    1. Admin navega entre tabs no menu Configurações
    2. Status de Candidatos: lista editável de status
    3. Solicitação de Dados: configuração de campos solicitados
    4. Instruções LIA: governança + campos com toggles e instruções
  Estados de Botoes:
    - "Editar" / "Salvar" / "Cancelar" por seção
    - "Mostrar campos inativos" toggle
  Validacoes Inline:
    - Instrução > 500 chars — contador com alerta
  Mensagens de Feedback:
    - Toast "Configurações salvas com sucesso"
    - Toast "Erro ao salvar. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] CandidateStatusesTab implementado
  - [ ] DataRequestTab implementado
  - [ ] Governança LIA com 3 regras configuráveis
  - [ ] LIA Field Definitions com toggle e instruções
  - [ ] Contadores de campos ativos/inativos
  - [ ] API integrada para todos os endpoints
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] Tabs de navegação entre as 5 seções do menu Configurações
  - [ ] Status de candidatos editáveis (CRUD)
  - [ ] Dados solicitados configuráveis
  - [ ] 3 regras de governança LIA com toggles
  - [ ] Campos LIA com toggle ativo/inativo
  - [ ] Instruções customizadas por campo LIA
  - [ ] Contadores de campos ativos/inativos corretos
  - [ ] Toggle "Mostrar campos inativos"

Arquivos de Referencia (Prototipo Replit):
  - RecruitmentHub.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/settings/RecruitmentHub.tsx

Nota MVP (v1):
  - MVP v1: Governança LIA + LIA Field Definitions + Status de Candidatos
  - Pós-MVP: Solicitação de Dados avançada, templates de instruções LIA

Integracoes e Impactos:
  Componentes Afetados:
    - Comportamento da LIA nas triagens — governança define limites de autonomia
  Vinculacoes:
    - CFG-003 — status de candidatos podem ser usados nas etapas do pipeline
  Comportamentos Automaticos:
    - Governança LIA aplica regras automaticamente nas interações da LIA

Dados e Estado:
  Interfaces:
    - "GovernanceRules { autoScheduleInterviews, autoSendNegativeFeedback, requiresValidationBeforeShortlist }"
    - "LiaFieldDefinition { key, label, category, description, active, instructions? }"
  Campos:
    - governanceRules (GovernanceRules)
    - liaToggles (Record<string, boolean>)
    - liaInstructions (Record<string, string>)
  Estados do Componente:
    - loading, savingGovernance, savingLiaConfig: boolean
    - isEditingGovernance: boolean
    - showInactiveFields: boolean
    - liaLocalToggles, liaLocalInstructions: Record<string, any>

QA/Teste:
  Cenarios de Teste:
    - "Editar e salvar regras de governança"
    - "Toggle campo LIA ativo/inativo"
    - "Adicionar instrução customizada a campo LIA"
    - "CRUD de status de candidatos"
    - "Configurar dados solicitados"
  Casos Edge:
    - "Instrução > 500 chars — truncar ou alertar"
    - "Desativar todos os campos LIA — permitir com alerta"
    - "Network error ao salvar governança"
  Checklist de Regressao:
    - [ ] Governança reflete no comportamento da LIA
    - [ ] Status de candidatos disponíveis no pipeline

Bitbucket Commit:
  Branch: feature/CFG-010-config-status-dados-lia
  Commit Pattern: "[CFG-010] feat: implementar status candidatos, solicitação dados e instruções LIA"
  PR Checklist:
    - [ ] 3 tabs implementadas
    - [ ] Governança LIA
    - [ ] LIA Field Definitions
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar 3 tabs restantes no menu Configurações: Status de Candidatos, Solicitação de Dados, Instruções LIA.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência: plataforma-lia/src/components/settings/RecruitmentHub.tsx (linhas 1187-1510)

    1. CandidateStatusesTab: CRUD de status de candidatos
    2. DataRequestTab: configuração de dados solicitados (companyId)
    3. LiaInstructionsTab:
       a. Governança LIA (ShieldCheck): 3 v-switch (autoScheduleInterviews, autoSendNegativeFeedback, requiresValidationBeforeShortlist)
          API: POST /api/backend-proxy/company/governance-rules
       b. LIA Field Definitions: toggle campos + instruções customizadas por campo
          API: POST /api/backend-proxy/company/culture-profile
          LiaFieldToggle component: v-switch + v-textarea
          Contadores: X campos ativos, Y inativos
          Toggle "Mostrar campos inativos"
```

---

### CFG-011: Coluna Status de Triagem na Tabela de Vagas

```yaml
Titulo: "[FRONTEND] Coluna Status de Triagem na Tabela de Vagas"
Tipo: Feature
Area: Frontend
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 3
Prioridade: Alta
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-005

Descricao: |
  Nova coluna na tabela de vagas exibindo o status da triagem de cada vaga.
  5 estados possíveis com cores semânticas:
  - not_configured (cinza) — triagem não configurada
  - not_started (azul) — configurada mas não iniciada
  - active (verde) — triagem em andamento
  - paused (âmbar) — triagem pausada
  - completed (verde escuro) — triagem concluída

  Badge clicável que abre modal de detalhes.
  Vinculado a transições de status da vaga (CFG-012).

Historia de Usuario: |
  Como recrutador, eu quero ver o status da triagem diretamente na tabela de vagas
  para monitorar rapidamente quais vagas estão com triagem ativa, pausada ou pendente.

Regras de Negocio:
  1. Cada vaga tem um screeningStatus no tipo Job
  2. 5 estados com cores semânticas distintas
  3. Badge clicável abre modal com detalhes da triagem
  4. Status reflete impactos automáticos de mudança de status da vaga (CFG-012)
  5. Vaga duplicada reseta screeningStatus para not_configured

Requisitos Tecnicos:
  Frontend:
    - Nova coluna na tabela de vagas com v-chip clicável
    - Cores semânticas por estado
    - Modal de detalhes da triagem
    - Propriedade screeningStatus no tipo Job
  Backend:
    - Campo screening_status no modelo Job (enum: not_configured, not_started, active, paused, completed)
    - Retornado no GET /api/v1/jobs e GET /api/v1/jobs/:id
  Dados:
    - "screeningStatus: 'not_configured' | 'not_started' | 'active' | 'paused' | 'completed'"
    - Mapeamento de cores por estado
  Validacoes:
    - screeningStatus deve ser um dos 5 valores válidos
    - Default: 'not_configured'

Design & Componentes:
  Componentes Existentes:
    - v-data-table, v-chip, v-dialog (Vuetify 3)
  Novos Componentes:
    - ScreeningStatusColumn.vue — coluna da tabela
    - ScreeningStatusBadge.vue — badge clicável com cor semântica
    - ScreeningDetailsModal.vue — modal de detalhes
  Design Tokens:
    - not_configured: bg-gray-100 text-gray-600
    - not_started: bg-blue-100 text-blue-700
    - active: bg-green-100 text-green-700
    - paused: bg-amber-100 text-amber-700
    - completed: bg-emerald-100 text-emerald-800
  Layout:
    - Coluna na tabela de vagas (largura ~140px)
    - Badge centralizado na célula
    - Modal com detalhes ao clicar
  Estados:
    - 5 estados visuais distintos
    - Modal aberto/fechado
  Acessibilidade:
    - Badge com aria-label "Status da triagem: [estado]"
    - Modal com focus trapping
    - Cores complementadas com texto (não apenas cor)

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador visualiza tabela de vagas
    2. Coluna "Status Triagem" exibe badge com cor por vaga
    3. Recrutador clica no badge para ver detalhes
    4. Modal abre com informações da triagem
  Estados de Botoes:
    - Badge clicável com cursor pointer
  Validacoes Inline:
    - Nenhuma (componente read-only)
  Mensagens de Feedback:
    - Labels por estado: "Não configurada", "Não iniciada", "Ativa", "Pausada", "Concluída"

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Coluna adicionada à tabela de vagas
  - [ ] 5 estados com cores semânticas
  - [ ] Badge clicável
  - [ ] Modal de detalhes
  - [ ] Testes unitários
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] Coluna "Status Triagem" visível na tabela de vagas
  - [ ] 5 estados com cores distintas (cinza, azul, verde, âmbar, verde escuro)
  - [ ] Badge mostra label do estado em português
  - [ ] Clicar no badge abre modal de detalhes
  - [ ] Status reflete mudanças automáticas (CFG-012)

Arquivos de Referencia (Prototipo Replit):
  - jobsPageTypes.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/jobs/jobsPageTypes.ts

Nota MVP (v1):
  - MVP v1: Coluna com badge e 5 estados
  - Pós-MVP: Filtro por status de triagem, ações rápidas no badge

Integracoes e Impactos:
  Componentes Afetados:
    - Tabela de Vagas — nova coluna adicionada
  Vinculacoes:
    - CFG-005 — ativar/pausar triagem atualiza status
    - CFG-012 — mudanças de status da vaga impactam status de triagem
  Comportamentos Automaticos:
    - Status atualiza automaticamente conforme regras do CFG-012

Dados e Estado:
  Interfaces:
    - "Job.screeningStatus: 'not_configured' | 'not_started' | 'active' | 'paused' | 'completed'"
  Campos:
    - screeningStatus (read-only display)
  Estados do Componente:
    - Nenhum estado interno (derivado de job.screeningStatus)

QA/Teste:
  Cenarios de Teste:
    - "Vaga sem triagem configurada — badge cinza 'Não configurada'"
    - "Vaga com triagem ativa — badge verde 'Ativa'"
    - "Vaga com triagem pausada — badge âmbar 'Pausada'"
    - "Clicar no badge abre modal"
    - "Status atualiza após mudança de status da vaga"
  Casos Edge:
    - "screeningStatus undefined — tratar como not_configured"
    - "Vaga duplicada — screeningStatus reseta para not_configured"
  Checklist de Regressao:
    - [ ] Tabela de vagas não quebra com nova coluna
    - [ ] Ordenação da tabela funciona com nova coluna
    - [ ] Modal fecha corretamente

Bitbucket Commit:
  Branch: feature/CFG-011-coluna-status-triagem
  Commit Pattern: "[CFG-011] feat: adicionar coluna status de triagem na tabela de vagas"
  PR Checklist:
    - [ ] Nova coluna na tabela
    - [ ] 5 estados com cores
    - [ ] Badge clicável + modal
    - [ ] Testes unitários
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Adicionar coluna "Status Triagem" na tabela de vagas.
    Badge clicável com 5 estados e cores semânticas.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referência: plataforma-lia/src/components/jobs/jobsPageTypes.ts (screeningStatus type)

    5 estados:
    - not_configured: cinza (bg-gray-100 text-gray-600) — "Não configurada"
    - not_started: azul (bg-blue-100 text-blue-700) — "Não iniciada"
    - active: verde (bg-green-100 text-green-700) — "Ativa"
    - paused: âmbar (bg-amber-100 text-amber-700) — "Pausada"
    - completed: verde escuro (bg-emerald-100 text-emerald-800) — "Concluída"

    v-chip clicável → abre v-dialog com detalhes da triagem
    Default: 'not_configured' quando undefined
    Vaga duplicada: resetar para 'not_configured'
```

---

### CFG-012: Integrações e Vinculações entre Componentes

```yaml
Titulo: "[FULL-STACK] Integrações e Vinculações entre Componentes"
Tipo: Feature
Area: Full-Stack
Sprint: A definir
Início: A definir
Término: A definir
Data Inicio Jira: A definir
Data Termino Jira: A definir
Pontos: 8
Prioridade: Crítica
Epic: EPIC-CFG
Status: 📋 Pendente Jira

Dependencias: CFG-001, CFG-002, CFG-003, CFG-004, CFG-005, CFG-006, CFG-007, CFG-008, CFG-009, CFG-010, CFG-011

Descricao: |
  Lógica de integração cross-cutting entre todos os componentes do épico. CARD CRÍTICO.

  1. Status Vaga ↔ Status Triagem:
     - getScreeningImpact(newStatus) determina impacto
     - Vaga "Paralisada" + triagem "active" → auto-pause, toast "Triagem pausada automaticamente"
     - Vaga "Concluída"/"Cancelada" + triagem active/paused/not_started → auto-complete, toast "Triagem finalizada automaticamente"
     - Vaga "Ativa" vinda de "Paralisada" + triagem "paused" → ask_reactivate dialog, opção reativar, toast "Triagem reativada automaticamente"
     - handleStatusChangeWithScreening() orquestra o fluxo
     - statusChangeConfirm state para dialog de confirmação
     - Vaga duplicada → triagem reseta para not_configured

  2. Campos da Vaga → Perguntas Derivadas:
     - useEffect/watch: job.languages, job.workModel, job.type, job.location, job.isAffirmative, job.affirmativeCriteriaPrimary
     - generateDerivedQuestions(job) cria perguntas a partir dos campos preenchidos
     - Merge preserva toggle state via prevMap ao regenerar
     - Placeholders: {modeloTrabalho}, {tipoContratação}, {localização}, {idioma}, {nível}
     - resolveTemplate() para substituição de placeholders
     - Perguntas afirmativas com variantes por critério (PCD, gênero, raça, idade, LGBTQIA+)

  3. Pipeline Empresa → Processo Seletivo Vaga:
     - getCompanyPipelineStages() fornece defaults
     - rawStages.length > 0 usa etapas da vaga, senão usa pipeline da empresa
     - Filtra etapas ativas, mapeia para formato de etapa da vaga com order

  4. Banco Central → Perguntas na Triagem:
     - ELIGIBILITY_QUESTIONS_BANK é single source of truth
     - System defaults (isSystemDefault: true) → DerivedQuestions
     - Non-system defaults → CompanyBankQuestions (filtered: !q.isSystemDefault)
     - Bank overrides persistem via bankQuestionOverrides state
     - QUESTION_CATEGORIES para agrupamento (9 categorias)

  5. Screening Progress Tracking:
     - screeningCompletion: {configuracoes, descricao, perguntas} booleans
     - progressCount = count of true values (0-3)

Historia de Usuario: |
  Como recrutador, eu quero que as mudanças em uma parte do sistema reflitam automaticamente nas partes relacionadas
  para que as configurações sejam consistentes e eu não precise atualizar manualmente cada componente.

Regras de Negocio:
  1. Paralisar vaga com triagem ativa → pausa automática da triagem
  2. Concluir/Cancelar vaga → finaliza triagem automaticamente
  3. Reativar vaga paralisada com triagem pausada → dialog pergunta se quer reativar triagem
  4. Duplicar vaga → triagem reseta para not_configured
  5. Alterar campos de triagem (workModel, type, location, languages, isAffirmative) → regenera perguntas derivadas
  6. Regenerar perguntas preserva toggles anteriores via merge map
  7. Vaga sem etapas → herda pipeline da empresa
  8. Banco central é fonte única para perguntas de elegibilidade
  9. System defaults → DerivedQuestions, non-system → CompanyBankQuestions
  10. Progresso de triagem rastreia 3 indicadores independentes

Requisitos Tecnicos:
  Frontend:
    - Composable useScreeningImpact para lógica de impacto
    - Watch/computed para regeneração de perguntas derivadas
    - Composable useCompanyPipeline para fallback de etapas
    - Composable useScreeningProgress para tracking de progresso
    - Dialog de confirmação reutilizável para mudanças de status
  Backend:
    - PUT /api/v1/jobs/:id — atualizar status da vaga E screening_status atomicamente
    - Validação de transições de status válidas
    - Endpoint para duplicação de vaga com reset de screening
  Dados:
    - "getScreeningImpact(newStatus): 'pause' | 'complete' | 'ask_reactivate' | 'none'"
    - "handleStatusChangeWithScreening(newStatus, reactivateScreening?)"
    - "generateDerivedQuestions(job): DerivedQuestion[]"
    - "resolveTemplate(template, replacements): string"
    - "screeningCompletion: { configuracoes: boolean, descricao: boolean, perguntas: boolean }"
  Validacoes:
    - Transições de status válidas
    - Perguntas derivadas consistentes com campos preenchidos
    - Progresso calculado corretamente

Design & Componentes:
  Componentes Existentes:
    - Todos os componentes dos cards CFG-001 a CFG-011
  Novos Componentes:
    - StatusChangeConfirmDialog.vue — dialog de confirmação com impacto na triagem
    - ScreeningImpactIndicator.vue — indicador visual do impacto
  Design Tokens:
    - impact-pause: bg-amber-100 (Pause icon)
    - impact-complete: bg-blue-100 (CheckCircle2 icon)
    - impact-reactivate: bg-green-100 (Play icon)
  Layout:
    - Dialog de confirmação centralizado com informações de impacto
    - Indicadores de impacto dentro do dialog
  Estados:
    - statusChangeConfirm: { newStatus, screeningImpact } | null
    - Dialog aberto/fechado
    - Opção de reativação (para ask_reactivate)
  Acessibilidade:
    - Dialog com focus trapping
    - Informações de impacto com aria-live
    - Botões com labels descritivos

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador altera status da vaga
    2. Sistema verifica impacto na triagem via getScreeningImpact()
    3. Se impacto !== 'none', dialog de confirmação é exibido
    4. Dialog mostra mensagem específica por tipo de impacto
    5. Recrutador confirma ou cancela
    6. Se confirma, handleStatusChangeWithScreening() executa mudanças
    7. Toast informa resultado
  Estados de Botoes:
    - "Confirmar" — executa mudança com impacto
    - "Cancelar" — fecha dialog sem mudanças
    - "Sim, reativar triagem" — para ask_reactivate
    - "Não, manter pausada" — para ask_reactivate sem reativação
  Validacoes Inline:
    - Nenhuma (lógica automática)
  Mensagens de Feedback:
    - "Triagem pausada automaticamente" (ao paralisar vaga)
    - "Triagem finalizada automaticamente" (ao concluir/cancelar vaga)
    - "Triagem reativada automaticamente" (ao reativar com confirmação)
    - "Status da vaga alterado" (sem impacto na triagem)

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] getScreeningImpact() implementado com todas as regras
  - [ ] handleStatusChangeWithScreening() orquestra mudanças
  - [ ] Dialog de confirmação com mensagens por tipo de impacto
  - [ ] generateDerivedQuestions() com merge de toggles
  - [ ] resolveTemplate() para placeholders
  - [ ] Fallback de pipeline empresa
  - [ ] Banco central → DerivedQuestions/CompanyBankQuestions
  - [ ] Screening progress tracking
  - [ ] Duplicação reseta screening
  - [ ] Testes unitários com cobertura > 90%
  - [ ] Testes de integração
  - [ ] Code review aprovado

Criterios de Aceitacao:
  - [ ] Paralisar vaga ativa com triagem ativa → pausa automática + toast
  - [ ] Concluir vaga com triagem ativa → finaliza automática + toast
  - [ ] Cancelar vaga com triagem pausada → finaliza automática + toast
  - [ ] Reativar vaga paralisada com triagem pausada → dialog com opção de reativação
  - [ ] Duplicar vaga → screening reseta para not_configured
  - [ ] Alterar workModel → regenera pergunta derivada sobre modelo de trabalho
  - [ ] Alterar languages → regenera perguntas derivadas por idioma obrigatório
  - [ ] Alterar isAffirmative → gera/remove pergunta afirmativa com critério específico
  - [ ] Toggle de pergunta derivada preservado ao regenerar
  - [ ] Vaga sem etapas → herda pipeline da empresa
  - [ ] System defaults do banco → DerivedQuestions
  - [ ] Non-system do banco → CompanyBankQuestions
  - [ ] 3 indicadores de progresso corretos

Arquivos de Referencia (Prototipo Replit):
  - JobEditTab.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/jobs/JobEditTab.tsx
  - ScreeningConfigManager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx
  - DerivedQuestions.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/DerivedQuestions.tsx

Nota MVP (v1):
  - MVP v1: Todas as integrações implementadas — este card é critical path
  - Pós-MVP: Integrações avançadas com webhook notifications, audit log de mudanças automáticas

Integracoes e Impactos:
  Componentes Afetados:
    - Todos os componentes CFG-001 a CFG-011
  Vinculacoes:
    - CFG-002 — status da vaga dispara impacto na triagem
    - CFG-003 — herança de pipeline empresa
    - CFG-005 — ativar/pausar triagem
    - CFG-007 — perguntas derivadas e banco
    - CFG-009 — banco central como source of truth
    - CFG-011 — badge de status reflete mudanças
  Comportamentos Automaticos:
    - Auto-pause de triagem ao paralisar vaga
    - Auto-complete de triagem ao concluir/cancelar vaga
    - Regeneração de perguntas derivadas ao alterar campos
    - Herança de pipeline empresa como fallback
    - Reset de screening ao duplicar vaga

Dados e Estado:
  Interfaces:
    - "getScreeningImpact(newStatus: string): 'pause' | 'complete' | 'ask_reactivate' | 'none'"
    - "handleStatusChangeWithScreening(newStatus: string, reactivateScreening?: boolean): void"
    - "generateDerivedQuestions(job: Job): DerivedQuestion[]"
    - "resolveTemplate(template: string, replacements: Record<string, string>): string"
  Campos:
    - statusChangeConfirm: { newStatus: string, screeningImpact: string } | null
    - screeningCompletion: { configuracoes: boolean, descricao: boolean, perguntas: boolean }
    - derivedQuestions: DerivedQuestion[]
  Estados do Componente:
    - Dialog de confirmação aberto/fechado
    - Progresso: 0/3, 1/3, 2/3, 3/3

QA/Teste:
  Cenarios de Teste:
    - "Paralisar vaga com triagem active → pausa automática"
    - "Concluir vaga com triagem active → finaliza automática"
    - "Cancelar vaga com triagem paused → finaliza automática"
    - "Cancelar vaga com triagem not_started → finaliza automática"
    - "Reativar vaga paralisada com triagem paused → dialog ask_reactivate"
    - "Escolher 'Sim, reativar' → triagem volta para active"
    - "Escolher 'Não, manter pausada' → triagem fica paused"
    - "Alterar workModel → pergunta derivada gerada com placeholder correto"
    - "Alterar languages com 2 idiomas obrigatórios → 2 perguntas derivadas"
    - "Alterar isAffirmative com PCD → pergunta específica PCD"
    - "Toggle disable em pergunta derivada → preservado após regenerar"
    - "Vaga sem etapas + empresa com pipeline → herda pipeline"
    - "System default no banco → aparece em DerivedQuestions"
    - "Non-system no banco → aparece em CompanyBankQuestions"
    - "Duplicar vaga → screeningStatus = not_configured"
    - "3 indicadores de progresso corretos em cada cenário"
  Casos Edge:
    - "Vaga sem screeningStatus → tratar como not_configured"
    - "Alterar status sem impacto → nenhum dialog, toast simples"
    - "Regenerar perguntas derivadas com campo removido → pergunta desaparece"
    - "Banco central vazio → CompanyBankQuestions vazio sem erro"
    - "Pipeline empresa vazio → lista vazia de etapas"
    - "Todos os 3 indicadores true → progressCount = 3"
    - "Nenhum indicador true → progressCount = 0"
  Checklist de Regressao:
    - [ ] Todos os flows de impacto funcionam após alterações em qualquer card
    - [ ] Perguntas derivadas consistentes após múltiplas edições de campos
    - [ ] Pipeline herança funciona após alterações no CFG-008
    - [ ] Banco central reflete alterações do CFG-009
    - [ ] Badge de status (CFG-011) atualiza em todos os cenários
    - [ ] Progresso de triagem atualiza em todos os cenários

Bitbucket Commit:
  Branch: feature/CFG-012-integracoes-vinculacoes
  Commit Pattern: "[CFG-012] feat: implementar integrações e vinculações cross-cutting"
  PR Checklist:
    - [ ] getScreeningImpact com todas as regras
    - [ ] handleStatusChangeWithScreening
    - [ ] Dialog de confirmação
    - [ ] generateDerivedQuestions com merge
    - [ ] resolveTemplate com placeholders PT-BR
    - [ ] Pipeline fallback
    - [ ] Banco central routing
    - [ ] Progress tracking
    - [ ] Testes unitários (>90%)
    - [ ] Testes de integração
    - [ ] Code review por 2 devs

Prompt de Desenvolvimento (Cursor/Claude Code):
  |
    Contexto: Implementar lógica de integração cross-cutting entre todos os componentes do épico CFG.
    CARD CRÍTICO — define como os componentes se comunicam e reagem a mudanças.

    Stack: Vue 3 + Nuxt 3 + Vuetify 3 + Ruby on Rails 7.x.

    Referências do protótipo Replit:
    - JobEditTab.tsx (linhas 136-175): getScreeningImpact, handleStatusChangeWithScreening, statusChangeConfirm
    - ScreeningConfigManager.tsx (linhas 82-98): screeningCompletion, progressCount
    - DerivedQuestions.tsx (linhas 41-155): generateDerivedQuestions, resolveTemplate, merge prevMap

    Implementar 5 composables Vue 3:

    1. useScreeningImpact(job, jobEditForm):
       - getScreeningImpact(newStatus) → 'pause' | 'complete' | 'ask_reactivate' | 'none'
       - handleStatusChangeWithScreening(newStatus, reactivateScreening?)
       - statusChangeConfirm state para dialog
       - Regras: Paralisada+active→pause, Concluída/Cancelada→complete, Ativa de Paralisada+paused→ask_reactivate

    2. useDerivedQuestions(job):
       - watch: job.languages, job.workModel, job.type, job.location, job.isAffirmative, job.affirmativeCriteriaPrimary
       - generateDerivedQuestions(job) com 5 system defaults
       - resolveTemplate(template, { modeloTrabalho, tipoContratação, localização, idioma, nível })
       - Merge preserva toggle via prevMap: new Map(prev.map(q => [q.id, q.enabled]))
       - Variantes afirmativas: PCD, gênero, raça, idade, LGBTQIA+

    3. useCompanyPipeline():
       - getCompanyPipelineStages()
       - rawStages.length > 0 ? rawStages : companyPipeline.filter(s => s.isActive).map(...)

    4. useEligibilityBank():
       - ELIGIBILITY_QUESTIONS_BANK como source of truth
       - getSystemDefaults() → isSystemDefault === true → DerivedQuestions
       - getNonSystemDefaults() → !isSystemDefault → CompanyBankQuestions
       - QUESTION_CATEGORIES (9 categorias)

    5. useScreeningProgress(screeningConfig, job, acceptedQuestions):
       - configDone = !!( channels || settings || scheduling configured)
       - jdDone = !!(description && description.trim().length > 0)
       - questionsDone = !!(screeningQuestions.length > 0 || acceptedQuestions.size > 0)
       - progressCount = [configDone, jdDone, questionsDone].filter(Boolean).length

    Dialog StatusChangeConfirmDialog.vue:
    - Mostra impacto com ícone: pause (Pause, âmbar), complete (CheckCircle2, azul), ask_reactivate (Play, verde)
    - Mensagens PT-BR: "Triagem pausada automaticamente", "Triagem finalizada automaticamente", "Triagem reativada automaticamente"
    - Para ask_reactivate: 2 botões "Sim, reativar" / "Não, manter pausada"
```

---

## DOCUMENTOS RELACIONADOS

| Documento | Descrição | Status |
|-----------|-----------|--------|
| [lia-mvp-cards-jira.md](./lia-mvp-cards-jira.md) | Cards Jira consolidados — Épicos 1-4, 10-11 | ✅ Ativo |
| [00-design-system-v4.md](../plataforma-lia/docs/design-system/00-design-system-v4.md) | Design System LIA v4.1 | ✅ Referência |
| [eligibility-questions-bank.ts](../plataforma-lia/src/components/settings/eligibility-questions-bank.ts) | Banco de perguntas de elegibilidade | ✅ Source of Truth |
| [types/benefits.ts](../plataforma-lia/src/types/benefits.ts) | Tipo canônico CompanyBenefit (14 campos) — Single Source of Truth | ✅ Referência |

---

**Nota:** Este documento é uma avaliação independente do Épico 5. Pendente revisão pelo time antes de ser incorporado ao documento principal `lia-mvp-cards-jira.md`.
