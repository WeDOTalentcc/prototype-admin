# Inventário Completo de Componentes — Plataforma LIA (React)

> **Última atualização:** 2026-03-27
> **Total:** 465 componentes em 80 diretórios
> **Localização:** `plataforma-lia/src/components/`
> **Stack:** React 19 + Next.js 15 + Tailwind CSS + shadcn/ui (Radix UI)

---

## 1. UI Base (`ui/`) — 68 componentes

Componentes primitivos reutilizáveis. Base do design system.

| # | Componente | Linhas | Tipo | Observação |
|---|-----------|--------|------|-----------|
| 1 | `accordion` | 58 | Primitivo | Radix Accordion |
| 2 | `ai-disclaimer` | 92 | Especializado | Disclaimer IA com ícone |
| 3 | `alert-dialog` | 141 | Primitivo | Radix AlertDialog |
| 4 | `audio-player` | 195 | Especializado | Player de áudio para entrevistas |
| 5 | `audio-record-button` | 176 | Especializado | Botão de gravação de áudio |
| 6 | `avatar` | 50 | Primitivo | Avatar com fallback de iniciais |
| 7 | `badge` | 102 | Primitivo | 8 variantes: default, secondary, destructive, outline, success, warning, info, lilac |
| 8 | `big-five-profile` | 171 | Especializado | Radar chart Big Five |
| 9 | `bulk-selection-bar` | 255 | Especializado | Barra de seleção em massa |
| 10 | `button` | 57 | Primitivo | 6 variantes + 4 tamanhos. Base do DS |
| 11 | `candidate-card` | 399 | Especializado | Card de candidato com score, tags, ações |
| 12 | `candidate-queries-guide` | 204 | Especializado | Guia de queries para candidatos |
| 13 | `card` | 79 | Primitivo | Card genérico com Header/Content/Footer |
| 14 | `chat-status-indicators` | 171 | Especializado | Indicadores de status do chat |
| 15 | `checkbox` | 30 | Primitivo | Radix Checkbox |
| 16 | `collapsible` | 11 | Primitivo | Radix Collapsible |
| 17 | `command-palette` | 2121 | Complexo | Ctrl+K — busca global, navegação, ações |
| 18 | `command` | 153 | Primitivo | Radix Command (base do palette) |
| 19 | `context-pill` | 84 | Especializado | Pill de contexto GLOBAL/CLIENTE |
| 20 | `data-request-indicator` | 47 | Especializado | Indicador de dados pendentes |
| 21 | `date-range-picker` | 356 | Especializado | Seletor de período com presets |
| 22 | `dialog` | 121 | Primitivo | Radix Dialog com overlay blur |
| 23 | `dropdown-menu` | 200 | Primitivo | Radix DropdownMenu |
| 24 | `empty-state` | 49 | Primitivo | Estado vazio genérico |
| 25 | `file-upload-button` | 235 | Especializado | Upload com preview e validação |
| 26 | `input` | 25 | Primitivo | Input text com forwardRef |
| 27 | `interview-rating` | 282 | Especializado | Componente de avaliação de entrevista |
| 28 | `interview-scheduling-modal` | 456 | Complexo | Modal de agendamento de entrevista |
| 29 | `label` | 26 | Primitivo | Radix Label |
| 30 | `lia-expanded-panel` | 540 | Complexo | Painel expandido da LIA |
| 31 | `lia-icon` | 63 | Primitivo | Ícone animado da LIA |
| 32 | `lia-queries-guide` | 298 | Especializado | Guia de queries LIA |
| 33 | `lia-search-queries-guide` | 312 | Especializado | Guia de queries de busca LIA |
| 34 | `lia-vacancy-queries-guide` | 275 | Especializado | Guia de queries de vagas LIA |
| 35 | `loading` | 132 | Primitivo | Skeleton + estados de loading |
| 36 | `pipeline-report` | 293 | Especializado | Relatório visual de pipeline |
| 37 | `pipeline-stages-carousel` | 206 | Especializado | Carrossel de etapas do pipeline |
| 38 | `popover` | 31 | Primitivo | Radix Popover |
| 39 | `premium-autocomplete` | 254 | Especializado | Autocomplete avançado |
| 40 | `progress` | 28 | Primitivo | Barra de progresso |
| 41 | `prompt-suggestions-dock` | 411 | Especializado | Dock de sugestões de prompt |
| 42 | `prompt-suggestions-popover` | 352 | Especializado | Popover de sugestões de prompt |
| 43 | `quick-action-chips` | 95 | Especializado | Chips de ação rápida |
| 44 | `radio-group` | 43 | Primitivo | Radix RadioGroup |
| 45 | `resizable-table-header` | 269 | Especializado | Header de tabela redimensionável |
| 46 | `score-icon-button` | 85 | Especializado | Botão com ícone de score |
| 47 | `scroll-area` | 47 | Primitivo | Radix ScrollArea customizado |
| 48 | `search-loading-animation` | 97 | Especializado | Animação de busca |
| 49 | `select` | 160 | Primitivo | Radix Select com variantes |
| 50 | `separator` | 30 | Primitivo | Divisor horizontal/vertical |
| 51 | `setup-alert-badge` | 207 | Especializado | Badge de alerta de setup pendente |
| 52 | `sheet` | 140 | Primitivo | Radix Sheet (drawer lateral) |
| 53 | `skeleton` | 15 | Primitivo | Skeleton loader |
| 54 | `slider` | 27 | Primitivo | Radix Slider |
| 55 | `status-badge` | 601 | Complexo | Badge de status do pipeline (17 cores de etapas) |
| 56 | `switch` | 28 | Primitivo | Radix Switch |
| 57 | `table` | 120 | Primitivo | Tabela base com Header/Body/Row/Cell |
| 58 | `tabs` | 55 | Primitivo | Radix Tabs com estilo pill |
| 59 | `textarea` | 23 | Primitivo | Textarea com forwardRef |
| 60 | `toast` | 129 | Primitivo | Toast com variantes |
| 61 | `toaster` | 35 | Primitivo | Container de toasts (Sonner) |
| 62 | `tooltip` | 30 | Primitivo | Radix Tooltip |
| 63 | `unified-bulk-actions-bar` | 200 | Especializado | Barra unificada de ações em massa |
| 64 | `variable-selector` | 267 | Especializado | Seletor de variáveis para templates |

---

## 2. Chat & LIA (`chat/`, `expanded-chat/`) — 22 componentes

Interface de conversação com a LIA.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `chat/action-result-card` | 175 | Card de resultado de ação executada pela LIA |
| 2 | `chat/agent-memory-indicator` | 326 | Indicador de memória do agente |
| 3 | `chat/chat-input-bar` | 122 | Barra de input do chat |
| 4 | `chat/detected-fields-card` | 75 | Card de campos detectados automaticamente |
| 5 | `chat/empty-field-notification-message` | 231 | Notificação de campos vazios |
| 6 | `chat/message-bubble` | 134 | Bolha de mensagem |
| 7 | `chat/message-feedback` | 230 | Feedback (like/dislike) em mensagens |
| 8 | `chat/multimodal-upload` | 333 | Upload multimodal (CV, imagens) |
| 9 | `chat/parecer-lia-card` | 305 | Card de parecer da LIA sobre candidato |
| 10 | `chat/resume-analysis-result` | 198 | Resultado de análise de currículo |
| 11 | `chat/typing-indicator` | 55 | Indicador de digitação da LIA |
| 12 | `chat/voice-chat-button` | 244 | Botão de chat por voz |
| 13 | `expanded-chat-modal` | 11824 | Modal principal do chat expandido (maior componente) |
| 14 | `expanded-chat/ExpandedChatContext` | 250 | Context provider do chat expandido |
| 15 | `expanded-chat/components/tool-confirmation-message` | 189 | Mensagem de confirmação de tool |
| 16 | `expanded-chat/components/tool-execution-feedback` | 165 | Feedback de execução de ferramenta |
| 17 | `expanded-chat/components/WizardHeader` | 177 | Header do wizard de criação de vaga |
| 18 | `expanded-chat/components/WizardSidebar` | 219 | Sidebar do wizard |
| 19 | `expanded-chat/components/WSIQualityBar` | 140 | Barra de qualidade WSI |
| 20 | `expanded-chat/modals/AddSkillModal` | 514 | Modal de adicionar skill |
| 21 | `expanded-chat/stages/CompetenciesStage` | 715 | Stage de competências do wizard |
| 22 | `expanded-chat/stages/EnrichedJDStage` | 478 | Stage de JD enriquecida |

---

## 3. Job Creation & Wizard (`job-creation/`, `job-wizard/`, `wizard/`, `job-description/`) — 28 componentes

Fluxo de criação e edição de vagas.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `job-creation/compensation-analysis-panel` | 605 | Análise de compensação/salário |
| 2 | `job-creation/compensation-chat-message` | 331 | Mensagem de chat sobre compensação |
| 3 | `job-creation/competencies-chat-message` | 291 | Mensagem sobre competências detectadas |
| 4 | `job-creation/confidence-indicator` | 128 | Indicador de confiança da IA |
| 5 | `job-creation/field-origin-badge` | 122 | Badge de origem do campo (manual/IA) |
| 6 | `job-creation/final-review-panel` | 501 | Painel de revisão final da vaga |
| 7 | `job-creation/jd-comparison-modal` | 519 | Modal de comparação de JD |
| 8 | `job-creation/jd-parser-result` | 1149 | Resultado do parser de JD |
| 9 | `job-creation/job-preview-card` | 301 | Preview do card de vaga |
| 10 | `job-creation/job-wizard-header` | 243 | Header do wizard |
| 11 | `job-creation/persona-card` | 205 | Card de persona do candidato ideal |
| 12 | `job-creation/smart-jd-editor` | 1076 | Editor inteligente de JD |
| 13 | `job-creation/smart-jd-section` | 488 | Seção inteligente com sugestões IA |
| 14 | `job-creation/smart-tags-field` | 381 | Campo de tags inteligentes |
| 15 | `job-creation/wizard-chat-panel` | 1064 | Painel de chat do wizard |
| 16 | `job-description/description-tab` | 1015 | Tab de descrição da vaga |
| 17 | `job-description/edit-job-drawer` | 1026 | Drawer de edição de vaga |
| 18 | `job-description/form-fields` | 735 | Campos do formulário de vaga |
| 19 | `job-description/jd-section-editor` | 373 | Editor de seção de JD |
| 20 | `job-wizard/wizard-ai-chat` | 1192 | Chat IA do wizard |
| 21 | `job-wizard/wizard-benefits-step` | 502 | Step de benefícios |
| 22 | `job-wizard/wizard-culture-step` | 428 | Step de cultura |
| 23 | `job-wizard/wizard-description-step` | 505 | Step de descrição |
| 24 | `job-wizard/wizard-overview-step` | 517 | Step de visão geral |
| 25 | `job-wizard/wizard-requirements-step` | 612 | Step de requisitos |
| 26 | `job-wizard/wizard-review-step` | 703 | Step de revisão final |
| 27 | `job-wizard/wizard-stepper` | 311 | Stepper visual do wizard |
| 28 | `wizard/suggestion-badge` | 146 | Badge de sugestão IA |

---

## 4. Candidatos (`candidate-*`, `cv/`, `triagem/`) — 15 componentes

Visualização, busca e triagem de candidatos.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `candidate-card` (ui) | 399 | Card resumo do candidato |
| 2 | `candidate-comparison` | 590 | Comparação lado a lado |
| 3 | `candidate-decision-flow-modal` | 524 | Modal de fluxo de decisão |
| 4 | `candidate-modal` | 655 | Modal completo do candidato |
| 5 | `candidate-page` | 2504 | Página completa do candidato |
| 6 | `candidate-preview` | 6723 | Preview expandido (2º maior componente) |
| 7 | `cv/cv-preview` | 641 | Preview de currículo |
| 8 | `cv/cv-upload-modal` | 473 | Modal de upload de CV |
| 9 | `triagem/pre-screening-config-drawer` | 345 | Drawer de configuração de triagem |
| 10 | `triagem/screening-interview-card` | 356 | Card de entrevista de triagem |
| 11 | `triagem/screening-pipeline-stats` | 252 | Estatísticas do pipeline de triagem |
| 12 | `triagem/screening-report-export` | 429 | Exportação de relatório de triagem |
| 13 | `triagem/triagem-detail-panel` | 764 | Painel de detalhe da triagem |
| 14 | `triagem/triagem-table` | 577 | Tabela de triagem |
| 15 | `triagem-details-modal` | 441 | Modal de detalhes da triagem |

---

## 5. Search & Sourcing (`search/`) — 17 componentes

Busca inteligente e sourcing de candidatos.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `search/BooleanBuilderModal` | 629 | Constructor de queries booleanas |
| 2 | `search/CandidateSourceSelector` | 211 | Seletor de fontes de candidatos |
| 3 | `search/city-suggestions-input` | 342 | Input de cidades com sugestões |
| 4 | `search/CityPresetsModal` | 434 | Modal de presets de cidades |
| 5 | `search/CompanyPresetsModal` | 561 | Modal de presets de empresas |
| 6 | `search/CompanySelectInput` | 370 | Input de seleção de empresa |
| 7 | `search/LanguagesFilterInput` | 278 | Filtro de idiomas |
| 8 | `search/SavedSearchCard` | 266 | Card de busca salva |
| 9 | `search/SaveSearchModal` | 183 | Modal para salvar busca |
| 10 | `search/search-results-card` | 497 | Card de resultado de busca |
| 11 | `search/SearchSourceSelector` | 155 | Seletor de fonte de busca |
| 12 | `search/SimilarProfilesInput` | 246 | Input de perfis similares |
| 13 | `search/SkillsFilterInput` | 370 | Filtro de skills |
| 14 | `search/smart-search-input` | 5475 | Input de busca inteligente (3º maior) |
| 15 | `search/TimezoneDropdown` | 170 | Dropdown de timezone |
| 16 | `search/UniversitiesFilterInput` | 460 | Filtro de universidades |
| 17 | `search/UniversityPresetsModal` | 729 | Modal de presets de universidades |

---

## 6. Pipeline & Kanban (`kanban/`, `pipeline/`, `jobs/`) — 17 componentes

Gestão visual do pipeline de recrutamento.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `kanban/candidate-kanban-card` | 310 | Card do candidato no kanban |
| 2 | `kanban/column-footer` | 155 | Footer da coluna do kanban |
| 3 | `kanban/kanban-board` | 548 | Board principal do kanban |
| 4 | `kanban/kanban-column` | 345 | Coluna do kanban com drag & drop |
| 5 | `kanban/kanban-header` | 146 | Header do kanban |
| 6 | `kanban/kanban-pagination` | 118 | Paginação do kanban |
| 7 | `kanban/stage-card` | 226 | Card de etapa do pipeline |
| 8 | `pipeline/pipeline-analytics` | 619 | Analytics do pipeline |
| 9 | `pipeline/pipeline-comparison` | 457 | Comparação de pipelines |
| 10 | `pipeline/pipeline-configuration` | 590 | Configuração de etapas |
| 11 | `pipeline/pipeline-stage-insights` | 423 | Insights por etapa |
| 12 | `jobs/job-card-enhanced` | 365 | Card de vaga aprimorado |
| 13 | `jobs/jobs-header` | 202 | Header da lista de vagas |
| 14 | `jobs/jobs-page` | 423 | Página principal de vagas |
| 15 | `jobs/jobs-stats` | 205 | Estatísticas de vagas |
| 16 | `jobs/jobs-table` | 316 | Tabela de vagas |
| 17 | `jobs/tab-content-with-actions` | 111 | Tab com ações contextuais |

---

## 7. Tables & Data Display (`tables/`) — 3 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `tables/candidate-table-row` | 229 | Row customizada de candidato |
| 2 | `tables/cell-renderers` | 780 | 30+ renderers de célula (score, status, actions, etc.) |
| 3 | `tables/unified-candidate-table` | 532 | Tabela unificada de candidatos |

---

## 8. Settings & Admin (`settings/`, `admin/`) — 32 componentes

Configurações, gestão de empresa, equipe e preferências.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `admin/AdminTemplateHub` | 829 | Hub de templates administrativos |
| 2 | `admin/ai-consumption/AgentBreakdown` | 73 | Breakdown de consumo por agente |
| 3 | `admin/ai-consumption/ConsumptionChart` | 51 | Gráfico de consumo IA |
| 4 | `admin/ai-consumption/ConsumptionGrid` | 48 | Grid de consumo |
| 5 | `admin/ai-consumption/ConsumptionSummaryCard` | 62 | Card resumo de consumo |
| 6 | `admin/Breadcrumbs` | 158 | Breadcrumbs admin |
| 7 | `admin/clients/ClientCard` | 105 | Card de cliente |
| 8 | `admin/clients/ClientFilters` | 95 | Filtros de clientes |
| 9 | `admin/clients/ClientTable` | 181 | Tabela de clientes |
| 10 | `admin/clients/CreateClientDialog` | 222 | Dialog de criar cliente |
| 11 | `admin/ClientSelector` | 188 | Seletor de cliente ativo |
| 12 | `admin/dashboard/ActivityFeed` | 65 | Feed de atividades admin |
| 13 | `admin/dashboard/MetricCard` | 59 | Card de métrica |
| 14 | `admin/dashboard/PeriodFilter` | 333 | Filtro de período |
| 15 | `admin/dashboard/QuickActions` | 69 | Ações rápidas |
| 16 | `admin/dashboard/ServiceConsumption` | 85 | Consumo de serviço |
| 17 | `admin/workos-admin-portal` | 86 | Portal admin WorkOS SSO |
| 18 | `admin/workos-link-card` | 54 | Card de link WorkOS |
| 19 | `settings/ApprovalsHub` | 522 | Hub de aprovações |
| 20 | `settings/BenefitsTab` | 1204 | Tab de benefícios |
| 21 | `settings/BigFiveRadar` | 216 | Radar Big Five da empresa |
| 22 | `settings/CommunicationHub` | 1796 | Hub de comunicações |
| 23 | `settings/CompanyDataCard` | 259 | Card de dados da empresa |
| 24 | `settings/CompanyDataSection` | 1036 | Seção completa dados empresa |
| 25 | `settings/CompanyTeamHub` | 5235 | Hub de equipe (4º maior) |
| 26 | `settings/CultureAnalyzer` | 610 | Analisador de cultura |
| 27 | `settings/CultureProfilePreview` | 671 | Preview do perfil cultural |
| 28 | `settings/DataRequestTab` | 978 | Tab de solicitação de dados |
| 29 | `settings/GlobalSearchHub` | 922 | Hub de busca global |
| 30 | `settings/GoalsPlanningHub` | 1050 | Hub de metas |
| 31 | `settings/RecruitmentHub` | 901 | Hub de recrutamento |
| 32 | `settings/SmartImportZone` | 584 | Zona de importação inteligente |

---

## 9. WSI — Weighted Screening Interview (`wsi/`) — 8 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `wsi/AdjustmentCounter` | 54 | Contador de ajustes em perguntas |
| 2 | `wsi/index` | 7 | Barrel export |
| 3 | `wsi/JDEvaluationPanel` | 1312 | Painel de avaliação de JD |
| 4 | `wsi/QuestionAdjustmentChat` | 250 | Chat de ajuste de perguntas |
| 5 | `wsi/QuestionDiffView` | 125 | Diff view de perguntas |
| 6 | `wsi/wsi-scorecard` | 314 | Scorecard WSI |
| 7 | `wsi/wsi-text-screening-modal` | 654 | Modal de triagem por texto |
| 8 | `wsi/wsi-triagem-invite-modal` | 805 | Modal de convite para triagem |

---

## 10. Dashboard & Analytics (`dashboard/`, `charts/`, `ml-analytics/`) — 11 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `dashboard/predictive-analytics-tab` | 554 | Tab de analytics preditivo |
| 2 | `dashboard/strategic-dashboard` | 534 | Dashboard estratégico |
| 3 | `dashboard-app` | 187 | App principal do dashboard |
| 4 | `charts/advanced-interactive-charts` | 679 | Gráficos interativos avançados |
| 5 | `charts/chart-components` | 239 | Componentes base de gráficos |
| 6 | `charts/interactive-charts` | 654 | Gráficos interativos |
| 7 | `ml-analytics/diversity-analytics` | 1008 | Analytics de diversidade |
| 8 | `ml-analytics/ml-analytics-dashboard` | 1106 | Dashboard de ML analytics |
| 9 | `ml-analytics/predictive-analytics` | 871 | Analytics preditivo |
| 10 | `ml-insights-card` | 174 | Card de insights ML |
| 11 | `lia-metrics-dashboard` | 524 | Dashboard de métricas LIA |

---

## 11. Interview & Notes (`interview-notes/`) — 5 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `interview-notes/create-adhoc-note-modal` | 220 | Modal de nota ad-hoc |
| 2 | `interview-notes/interview-note-card` | 495 | Card de nota de entrevista |
| 3 | `interview-notes/next-step-modal` | 387 | Modal de próximo passo |
| 4 | `interview-notes/scheduled-interview-activity-card` | 223 | Card de entrevista agendada |
| 5 | `interview-notes/score-card-wsi` | 410 | Scorecard WSI de entrevista |

---

## 12. Email & Communication (`email-templates/`, `communication/`) — 5 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `email-templates/email-template-form-modal` | 417 | Modal de formulário de template |
| 2 | `email-templates/email-templates-manager` | 564 | Gerenciador de templates |
| 3 | `email-templates/report-email-templates` | 713 | Templates de relatório por email |
| 4 | `email-templates/send-email-modal` | 325 | Modal de envio de email |
| 5 | `communication/message-composer` | 500 | Compositor de mensagens |

---

## 13. Talent Funnel (`talent-funnel-tabs/`) — 7 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `talent-funnel-tabs/favorites-tab` | 553 | Tab de favoritos |
| 2 | `talent-funnel-tabs/history-tab` | 394 | Tab de histórico |
| 3 | `talent-funnel-tabs/lists-tab` | 924 | Tab de listas de candidatos |
| 4 | `talent-funnel-tabs/saved-searches-tab` | 633 | Tab de buscas salvas |
| 5 | `talent-funnel-tabs/_archived/mapping-tab` | 1271 | Tab de mapeamento (arquivada) |
| 6 | `talent-funnel-tabs/_archived/personas-tab` | 1687 | Tab de personas (arquivada) |
| 7 | `talent-funnel-tabs/_archived/pipelines-tab` | 1069 | Tab de pipelines (arquivada) |

---

## 14. Autonomous & Proactive (`autonomous/`, `automation/`) — 5 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `autonomous/create-job-modal` | 350 | Modal de criação autônoma de vaga |
| 2 | `autonomous/jobs-dashboard` | 346 | Dashboard de vagas autônomas |
| 3 | `autonomous/proactive-actions-bell` | 386 | Sino de ações proativas |
| 4 | `autonomous/proactive-actions` | 301 | Lista de ações proativas |
| 5 | `automation/ProactiveChatMessage` | 68 | Mensagem proativa no chat |

---

## 15. Layout & Navigation — 9 componentes (raiz)

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `sidebar` | 617 | Sidebar principal com navegação |
| 2 | `top-bar` | 386 | Top bar com avatar, notificações |
| 3 | `theme-provider` | 16 | Provider de tema claro/escuro |
| 4 | `theme-toggle` | 22 | Toggle de tema |
| 5 | `wedo-logo` | 13 | Logo WeDO |
| 6 | `error-boundary` | 112 | Boundary de erro global |
| 7 | `client-only` | 22 | Wrapper client-side only |
| 8 | `auth-context` | 21 | Context de autenticação |
| 9 | `clouds-background` | 195 | Background de nuvens (login) |

---

## 16. Componentes Standalone (raiz) — 30+ componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `activity-feed` | 506 | Feed de atividades |
| 2 | `ai-search-toggle` | 471 | Toggle de busca IA |
| 3 | `batch-approval-modal` | 946 | Modal de aprovação em lote |
| 4 | `big-five-modal` | 545 | Modal Big Five personality |
| 5 | `bulk-actions-bar` | 728 | Barra de ações em massa |
| 6 | `calibration-card` | 328 | Card de calibração |
| 7 | `column-configuration-modal` | 346 | Modal de configuração de colunas |
| 8 | `company-screening-settings` | 507 | Config de triagem da empresa |
| 9 | `contextual-actions-banner` | 172 | Banner de ações contextuais |
| 10 | `daily-briefing-card` | 564 | Card de briefing diário |
| 11 | `disc-assessment-modal` | 557 | Modal de assessment DISC |
| 12 | `events-section` | 440 | Seção de eventos |
| 13 | `expandable-ai-prompt` | 4308 | Prompt expansível da IA (5º maior) |
| 14 | `experience-highlight-card` | 247 | Card de destaque de experiência |
| 15 | `export-tools` | 325 | Ferramentas de exportação |
| 16 | `fairness-warning-banner` | 49 | Banner de aviso de fairness/viés |
| 17 | `global-search-modal` | 482 | Modal de busca global |
| 18 | `intelligence-notifications` | 404 | Notificações inteligentes |
| 19 | `interviews-section` | 202 | Seção de entrevistas |
| 20 | `job-actions-bar` | 116 | Barra de ações de vaga |
| 21 | `lia-activity-feed` | 389 | Feed de atividades da LIA |
| 22 | `lia-metrics-chart` | 284 | Gráfico de métricas LIA |
| 23 | `lia-performance-indicators` | 421 | Indicadores de performance LIA |
| 24 | `lia-processing-card` | 288 | Card de processamento LIA |
| 25 | `lia-score-card` | 151 | Scorecard LIA |
| 26 | `lia-screening-dialogue` | 487 | Diálogo de triagem LIA |
| 27 | `lia-suggestion-cards` | 272 | Cards de sugestão da LIA |
| 28 | `lia-tips-modal` | 288 | Modal de dicas LIA |
| 29 | `task-modal` | 90 | Modal de tarefa |
| 30 | `war-room` | 461 | War room de recrutamento |
| 31 | `work-model-charts` | 415 | Gráficos de modelo de trabalho |

---

## Resumo por Números

| Categoria | Componentes | Linhas totais |
|-----------|------------|---------------|
| UI Base (primitivos + especializados) | 64 | ~12.300 |
| Chat & LIA | 22 | ~16.500 |
| Job Creation & Wizard | 28 | ~14.200 |
| Candidatos & Triagem | 15 | ~13.900 |
| Search & Sourcing | 17 | ~10.400 |
| Pipeline & Kanban | 17 | ~5.800 |
| Tables & Data | 3 | ~1.500 |
| Settings & Admin | 32 | ~16.300 |
| WSI | 8 | ~3.500 |
| Dashboard & Analytics | 11 | ~6.500 |
| Interviews & Notes | 5 | ~1.700 |
| Email & Communication | 5 | ~2.500 |
| Talent Funnel | 7 | ~5.500 |
| Autonomous & Proactive | 5 | ~1.400 |
| Layout & Navigation | 9 | ~1.400 |
| Standalone (raiz) | 30+ | ~12.000 |
| **TOTAL** | **~465** | **~125.000** |

---

## Top 10 Maiores Componentes

| # | Componente | Linhas | Observação |
|---|-----------|--------|-----------|
| 1 | `expanded-chat-modal` | 11.824 | Chat expandido — candidato a refactoring |
| 2 | `candidate-preview` | 6.723 | Preview de candidato — muita lógica inline |
| 3 | `smart-search-input` | 5.475 | Busca inteligente com NLP |
| 4 | `CompanyTeamHub` | 5.235 | Gestão de equipe |
| 5 | `expandable-ai-prompt` | 4.308 | Prompt expansível |
| 6 | `candidate-page` | 2.504 | Página do candidato |
| 7 | `goals-management` | 2.302 | Gestão de metas |
| 8 | `command-palette` | 2.121 | Paleta de comandos Ctrl+K |
| 9 | `CommunicationHub` | 1.796 | Hub de comunicações |
| 10 | `personas-tab` (archived) | 1.687 | Tab de personas (arquivada) |
