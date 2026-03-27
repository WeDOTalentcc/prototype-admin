# Inventário Completo de Componentes — Plataforma LIA (React)

> **Última atualização:** 2026-03-27 (Fase 0 aplicada — código morto removido)
> **Total:** 460 componentes em 76 diretórios (era 465 — removidos 5 arquivados + sedPT8vmF + 7 stories)
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

---

## 17. Análise de Potencial de Otimização

> Dados extraídos automaticamente do codebase em 2026-03-27.
> Nenhuma das otimizações abaixo altera o visual do produto — são refatorações internas.

### 17.1 Cores Hardcoded — 298 cores hex em 1.607 linhas

O maior problema de padronização. Cores são escritas diretamente nos componentes em vez de usar tokens do `design-tokens.css` ou classes Tailwind. Isso significa que uma mudança de cor no design system **não se propaga** automaticamente.

**Tabela: Top 30 cores mais usadas com mapeamento para token**

| # | Hex Hardcoded | Usos | Token CSS Equivalente | Classe Tailwind Equivalente | Contexto |
|---|--------------|------|----------------------|----------------------------|----------|
| 1 | `#374151` | 120 | `--lia-border-default` | `text-gray-700` / `border-gray-700` | Borders, texto secundário escuro |
| 2 | `#FFFFFF` | 96 | `--lia-bg-primary` | `bg-white` / `text-white` | Backgrounds, texto em fundo escuro |
| 3 | `#6B7280` | 78 | `--wedo-text-muted` | `text-gray-500` | Placeholders, hints, labels muted |
| 4 | `#111827` | 75 | `--lia-text-primary` | `text-gray-900` | Títulos, texto principal |
| 5 | `#F59E0B` | 70 | `--wedo-amber` | `text-amber-500` | Warnings, alertas |
| 6 | `#D1D5DB` | 69 | `--lia-text-disabled` | `text-gray-300` | Disabled, dividers claros |
| 7 | `#E5E7EB` | 65 | `--lia-border-subtle` | `border-gray-200` | Borders sutis |
| 8 | `#e5e7eb` | 51 | (duplicata case-insensitive do #7) | `border-gray-200` | Mesmo uso, casing diferente |
| 9 | `#EF4444` | 48 | — | `text-red-500` | Error, destructive |
| 10 | `#9CA3AF` | 46 | `--lia-text-tertiary` | `text-gray-400` | Texto terciário, ícones muted |
| 11 | `#F3F4F6` | 42 | `--lia-bg-tertiary` | `bg-gray-100` | Backgrounds hover, disabled |
| 12 | `#1a1a1a` | 38 | — | `text-gray-900` (aprox.) | Dark mode, fundo escuro |
| 13 | `#5DA47A` | 36 | `--wedo-green` | — (custom) | Candidatos, sucesso WeDo |
| 14 | `#EEEEEE` | 35 | — | `bg-gray-200` (aprox.) | Backgrounds neutros |
| 15 | `#22C55E` | 33 | — | `text-green-500` | Success |
| 16 | `#8B5CF6` | 28 | `--wedo-purple` (aprox.) | `text-violet-500` | Insights, premium |
| 17 | `#10B981` | 27 | — | `text-emerald-500` | Score alto, WSI positivo |
| 18 | `#F5F5F5` | 26 | — | `bg-neutral-100` | Backgrounds neutros |
| 19 | `#1F2937` | 24 | `--wedo-text-body` | `text-gray-800` | Texto corpo |
| 20 | `#60BED1` | 22 | `--wedo-cyan` | — (custom) | LIA, IA, destaque inteligente |
| 21 | `#E8E8E8` | 18 | — | `bg-gray-200` (aprox.) | Dividers, fundos |
| 22 | `#D5BFA8` | 18 | — | — | Cor sépia do pipeline |
| 23 | `#3B82F6` | 18 | — | `text-blue-500` | Info, links |
| 24 | `#0A66C2` | 18 | — | — | LinkedIn blue (manter hardcoded) |
| 25 | `#999999` | 17 | — | `text-gray-400` (aprox.) | Legado, cinza genérico |
| 26 | `#A8CED5` | 16 | `--lia-info-light` | — | Background info sutil |
| 27 | `#1f2937` | 16 | (duplicata case-insensitive do #19) | `text-gray-800` | Mesmo uso |
| 28 | `#E5A853` | 15 | `--lia-cat-interviews` | — | Entrevistas, LIA |
| 29 | `#D19960` | 15 | `--wedo-orange` | — (custom) | Alertas WeDo |
| 30 | `#6B9BD1` | 15 | — | — | Cor de pipeline específica |

**Top 20 arquivos com mais cores hardcoded:**

| # | Arquivo | Cores hardcoded | Comentário |
|---|---------|----------------|-----------|
| 1 | `search/smart-search-input.tsx` | 151 | Maior ofensor — paleta de filtros e sugestões |
| 2 | `ui/status-badge.tsx` | 90 | Paleta de 17 etapas do pipeline |
| 3 | `pages/job-kanban-page.tsx` | 87 | Cores de colunas e cards do kanban |
| 4 | `settings/archived/onboarding-wizard.tsx` | 63 | Arquivo arquivado — deletar resolve |
| 5 | `triagem-details-modal.tsx` | 47 | Cores de scores e status |
| 6 | `pages/jobs-page.tsx` | 45 | Cores de status de vagas |
| 7 | `email-templates/report-email-templates.tsx` | 44 | Cores de templates HTML |
| 8 | `pages/big-five-dashboard-page.tsx` | 39 | Radar chart cores |
| 9 | `rubric-evaluation-modal.tsx` | 37 | Escala de avaliação |
| 10 | `pages/candidates-page.tsx` | 37 | Cores de cards e badges |
| 11 | `ui/prompt-suggestions-dock.tsx` | 35 | Paleta de sugestões |
| 12 | `expandable-ai-prompt.tsx` | 34 | Cores de ações e contexto |
| 13 | `candidate-preview.tsx` | 30 | Seções e scores |
| 14 | `candidate-page.tsx` | 30 | Página do candidato |
| 15 | `ui/lia-search-queries-guide.tsx` | 28 | Guia de queries |
| 16 | `lia-float/LiaSuperPrompt.tsx` | 28 | Prompt flutuante |
| 17 | `ui/lia-vacancy-queries-guide.tsx` | 27 | Guia de queries de vagas |
| 18 | `ui/lia-queries-guide.tsx` | 27 | Guia de queries LIA |
| 19 | `ui/candidate-queries-guide.tsx` | 27 | Guia de queries candidatos |
| 20 | `agent-control-center/index.tsx` | 27 | Painel de agentes |

### 17.2 Valores Arbitrários Tailwind — 4.765 ocorrências

Valores como `text-[11px]`, `w-[300px]`, `h-[42px]` escritos diretamente em vez de usar classes do design system. Impossibilita mudança global de tamanhos.

**Distribuição de tamanhos de texto arbitrários:**

| Valor | Usos | % do total | Mapeamento proposto |
|-------|------|-----------|-------------------|
| `text-[11px]` | 2.307 | 48.4% | Criar `text-ui` no tailwind.config |
| `text-[10px]` | 1.670 | 35.0% | Criar `text-micro` |
| `text-[9px]` | 368 | 7.7% | Criar `text-tiny` (avaliar remoção — acessibilidade) |
| `text-[13px]` | 186 | 3.9% | Criar `text-base-ui` ou usar `text-sm` |
| `text-[14px]` | 65 | 1.4% | Usar `text-sm` (já é 14px no Tailwind default) |
| `text-[8px]` | 25 | 0.5% | Eliminar — muito pequeno para WCAG AA |
| `text-[16px]` | 23 | 0.5% | Usar `text-base` |
| `text-[18px]` | 22 | 0.5% | Usar `text-lg` |
| `text-[12px]` | 18 | 0.4% | Usar `text-xs` |
| `text-[20px]` | 13 | 0.3% | Usar `text-xl` |
| `text-[7px]` | 1 | — | Eliminar |
| Outros (15, 24, 28, 32px) | 12 | — | Usar classes Tailwind padrão |
| **Total** | **4.710** | | |

**Distribuição de larguras arbitrárias (top 10):**

| Valor | Usos | Mapeamento proposto |
|-------|------|-------------------|
| `w-[200px]` | 29 | `w-[12.5rem]` ou criar token `w-sidebar-content` |
| `w-[300px]` | 23 | `w-[18.75rem]` ou criar token `w-panel-sm` |
| `w-[100px]` | 14 | `w-24` (96px) ou `w-[6.25rem]` |
| `w-[180px]` | 13 | Criar token se recorrente |
| `w-[350px]` | 12 | Criar token `w-panel-md` |
| `w-[400px]` | 10 | `w-[25rem]` ou criar token `w-panel-lg` |
| `w-[500px]` | 8 | Criar token `w-panel-xl` |
| `w-[280px]` | 8 | `w-72` (288px, próximo) |
| `w-[80px]` | 7 | `w-20` (80px — equivalente exato) |
| `w-[420px]` | 7 | Criar token se recorrente |

**Distribuição de alturas arbitrárias (top 10):**

| Valor | Usos | Mapeamento proposto |
|-------|------|-------------------|
| `h-[200px]` | 16 | `h-[12.5rem]` ou token `h-chart` |
| `h-[100px]` | 16 | `h-24` (96px, próximo) |
| `h-[400px]` | 13 | Token `h-panel-lg` |
| `h-[300px]` | 11 | Token `h-panel-md` |
| `h-[180px]` | 11 | Token `h-card-lg` |
| `h-[120px]` | 9 | `h-[7.5rem]` |
| `h-[280px]` | 7 | `h-72` (288px, próximo) |
| `h-[60px]` | 6 | `h-[3.75rem]` ou `h-15` |
| `h-[80px]` | 5 | `h-20` (80px — equivalente exato) |
| `h-[56px]` | 5 | `h-14` (56px — equivalente exato) |

### 17.3 Componentes Gigantes — 37 arquivos > 1.000 linhas = 118.037 linhas

Representam **94% de todo o código** de componentes. Cada um mistura lógica de negócio, state management, UI, e estilo. Dificulta testes, manutenção e conversão para Vue.

| # | Componente | Linhas | Categoria | Proposta de Split |
|---|-----------|--------|-----------|-----------------|
| 1 | `expanded-chat-modal` | 11.824 | Chat | → WizardChat, MessageList, InputBar, ToolResults, StageManager, StateReducer, FieldSync, JobPreview (~8-10 sub) |
| 2 | `pages/job-kanban-page` | 10.377 | Pipeline | → KanbanBoard, KanbanColumn, CandidateCard, Filters, BulkActions, StageConfig, Analytics (~7 sub) |
| 3 | `pages/candidates-page` | 10.329 | Candidatos | → CandidateTable, FilterPanel, BulkActions, PreviewPanel, SearchBar, Pagination (~6 sub) |
| 4 | `pages/jobs-page` | 8.046 | Vagas | → JobsTable, JobCard, Filters, Stats, BulkActions, CreateButton (~6 sub) |
| 5 | `candidate-preview` | 6.723 | Candidatos | → ProfileHeader, Timeline, Skills, WSI, Notes, Actions, Tabs (~7 sub) |
| 6 | `pages/chat-page` | 5.592 | Chat | → ChatContainer, MessageList, InputBar, VoiceChat, Suggestions (~5 sub) |
| 7 | `search/smart-search-input` | 5.475 | Search | → SearchBar, FilterChips, Suggestions, BooleanBuilder, Results (~5 sub) |
| 8 | `settings/CompanyTeamHub` | 5.235 | Settings | → TeamTable, InviteModal, RoleManager, Permissions, ActivityLog (~5 sub) |
| 9 | `pages/settings-page` | 4.449 | Settings | → TabManager + cada tab como componente separado (~8 sub) |
| 10 | `expandable-ai-prompt` | 4.308 | LIA | → PromptInput, SuggestionDock, AttachmentBar, ActionChips (~4 sub) |
| 11 | `pages/dashboards-page` | 3.283 | Dashboard | → DashboardGrid, MetricCards, Charts, Filters (~4 sub) |
| 12 | `search/advanced-filters-modal` | 3.282 | Search | → FilterGroups, FilterField, SavedFilters (~3 sub) |
| 13 | `candidate-page` | 2.504 | Candidatos | → ProfileSections, Timeline, Actions (~3 sub) |
| 14 | `screening-config/ScreeningConfigManager` | 2.402 | Triagem | → ConfigForm, QuestionEditor, Preview (~3 sub) |
| 15 | `settings/goals-management` | 2.302 | Settings | → GoalsList, GoalForm, GoalProgress (~3 sub) |
| 16 | `pages/tasks-page` | 2.192 | Tasks | → TaskList, TaskForm, TaskFilters (~3 sub) |
| 17 | `quick-actions-modals` | 2.076 | Modals | → Cada modal como componente individual (~5 sub) |
| 18 | `modals/edit-job-modal` | 1.989 | Modals | → Tabs de edição como sub-componentes (~4 sub) |
| 19 | `settings/archived/onboarding-wizard` | 1.905 | Archived | → DELETAR (código morto) |
| 20 | `settings/CommunicationHub` | 1.796 | Settings | → TemplateList, TemplateEditor, Preview (~3 sub) |
| 21 | `pages/indicators-page` | 1.753 | Dashboard | → IndicatorCards, Charts, Filters (~3 sub) |
| 22 | `jobs/JobEditTab` | 1.727 | Vagas | → FormSections, FieldGroups (~3 sub) |
| 23 | `talent-funnel-tabs/_archived/personas-tab` | 1.687 | Archived | → DELETAR (código morto) |
| 24 | `pages/ats-integrations-page` | 1.522 | Settings | → IntegrationCard, ConfigForm (~2 sub) |
| 25 | `modals/job-insights-modal` | 1.496 | Modals | → InsightsSections, Charts (~3 sub) |
| 26 | `wsi/JDEvaluationPanel` | 1.312 | WSI | → EvalForm, ScoreDisplay, QuestionList (~3 sub) |
| 27 | `talent-funnel-tabs/_archived/mapping-tab` | 1.271 | Archived | → DELETAR (código morto) |
| 28 | `settings/BenefitsTab` | 1.204 | Settings | → BenefitsList, BenefitForm (~2 sub) |
| 29 | `triagem-details-modal` | 1.194 | Triagem | → TriagemHeader, ResultPanel, Actions (~3 sub) |
| 30 | `modals/new-candidate-unified-modal` | 1.162 | Modals | → CandidateForm, CVUpload, Preview (~3 sub) |
| 31 | `modals/job-status-modal` | 1.151 | Modals | → StatusForm, Checklist (~2 sub) |
| 32 | `lia-screening-guide` | 1.131 | LIA | → GuideSteps, Examples (~2 sub) |
| 33 | `pages/candidates/CandidatesFilterPanel` | 1.124 | Candidatos | → FilterGroups, FilterField (~2 sub) |
| 34 | `talent-funnel-tabs/_archived/pipelines-tab` | 1.069 | Archived | → DELETAR (código morto) |
| 35 | `modals/job-compare-modal` | 1.059 | Modals | → CompareGrid, MetricRow (~2 sub) |
| 36 | `settings/GoalsPlanningHub` | 1.050 | Settings | → PlanGrid, GoalCard (~2 sub) |
| 37 | `settings/CompanyDataSection` | 1.036 | Settings | → DataForm, DataCards (~2 sub) |

### 17.4 Código Morto — ~7.000 linhas em 8 arquivos

Componentes em pastas `archived/` ou `_archived/` que não são referenciados por nenhuma rota ativa.

| # | Arquivo | Linhas | Agravante |
|---|---------|--------|----------|
| 1 | `settings/archived/onboarding-wizard.tsx` | 1.905 | 63 cores hardcoded — o 4º pior ofensor |
| 2 | `talent-funnel-tabs/_archived/personas-tab.tsx` | 1.687 | Importa Chart.js desnecessariamente |
| 3 | `talent-funnel-tabs/_archived/mapping-tab.tsx` | 1.271 | Importa Chart.js |
| 4 | `talent-funnel-tabs/_archived/pipelines-tab.tsx` | 1.069 | Importa Chart.js |
| 5 | `pages/archived/learning-dashboard-page.tsx` | ~500 | Dashboard não utilizado |
| 6 | `pages/archived/jobs-page-dashboards-archived.tsx` | ~400 | Versão antiga da page |
| 7 | `archived/tabs-preview-vaga/lia-metrics-tab.tsx` | 321 | Tab removida |
| 8 | `archived/tabs-preview-vaga/screening-script-tab.tsx` | 671 | Tab removida |

**Ação:** Deletar todos. Zero impacto no produto. Reduz ~7.000 linhas e elimina imports desnecessários de Chart.js.

**Outros arquivos mortos:**
- `ui/sedPT8vmF` — arquivo espúrio com nome aleatório. Deletar.
- `ui/badge.stories.tsx`, `ui/button.stories.tsx`, `ui/card.stories.tsx`, `ui/dialog.stories.tsx`, `ui/input.stories.tsx`, `ui/select.stories.tsx` — 6 story files, Storybook instalado mas sem uso ativo. Avaliar se vale manter.

### 17.5 Duplicação de Badges e Status — 7 componentes similares

| # | Componente | Linhas | Função | Problema |
|---|-----------|--------|--------|---------|
| 1 | `ui/badge.tsx` | 102 | Badge primitivo, 8 variantes | Base correta, sem problemas |
| 2 | `ui/status-badge.tsx` | 601 | Badge de status do pipeline | 90 cores hardcoded, 17 tons de pipeline inline |
| 3 | `ui/setup-alert-badge.tsx` | 207 | Badge de setup pendente | Poderia usar badge.tsx como base |
| 4 | `job-creation/field-origin-badge.tsx` | 122 | Badge de origem (manual/IA) | Poderia usar badge.tsx como base |
| 5 | `wizard/suggestion-badge.tsx` | 146 | Badge de sugestão IA | Poderia usar badge.tsx como base |
| 6 | `screening/auto-screening-badge.tsx` | ~60 | Badge de screening automático | Poderia usar badge.tsx como base |
| 7 | `ui/chat-status-indicators.tsx` | 171 | Indicadores de status do chat | Padrão diferente mas relacionado |

**Recomendação:** Consolidar para 3 componentes:
1. `badge.tsx` — primitivo (manter como está)
2. `status-badge.tsx` — refatorar para usar tokens e badge.tsx como base
3. `indicator.tsx` — estados temporários (chat, loading)

### 17.6 Modais/Dialogs — 154 arquivos

154 componentes importam ou implementam Modal, Dialog, Drawer ou Sheet. Muitos reimplementam o mesmo padrão:
- Overlay com fundo escuro
- Formulário com campos
- Botões Cancel/Submit
- Validação e loading state

**Recomendação:** Criar padrão composable `FormDialog` que receba um schema de campos e gere o formulário automaticamente. Reduziria boilerplate em ~50% dos modais.

### 17.7 Inline Styles — 249 arquivos

249 dos 465 arquivos (54%) usam `style={}` inline. Problemas:
- Não responde a dark mode via classes CSS
- Não é responsivo
- Não é portável para Vue (onde scoped styles são preferidos)
- Dificulta override e customização

**Recomendação:** Converter gradualmente para classes Tailwind. Priorizar os componentes que aparecem em dark mode.

### 17.8 Resumo Quantitativo

| Problema | Escopo | Impacto na manutenção | Impacto na conversão Vue |
|----------|--------|----------------------|------------------------|
| 298 cores hardcoded | 1.607 linhas | **Alto** — cor muda no DS, não propaga | **Crítico** — cada cor precisa tradução manual |
| 4.765 valores arbitrários | text-[Xpx], w-[px], h-[px] | **Médio** — impossível mudar escala global | **Alto** — não tem equivalente no Vuetify |
| 37 componentes >1.000 linhas | 118.037 linhas (94% do total) | **Alto** — difícil testar e debugar | **Crítico** — impossível converter monólitos |
| 8 arquivos mortos | ~7.000 linhas | **Baixo** — ocupam espaço, confundem grep | **Nenhum** — não converter |
| 7 badges duplicados | ~1.400 linhas | **Médio** — inconsistência visual | **Alto** — precisa decidir qual é o canônico |
| 154 modais sem padrão | Espalhados | **Médio** — cada modal reinventa a roda | **Alto** — 154 conversões individuais |
| 249 arquivos com inline style | ~54% dos arquivos | **Alto** — dark mode quebra | **Crítico** — Vue usa scoped styles |

---

## 18. Plano de Otimização em 6 Fases

> Ordenado por: menor risco primeiro, maior impacto na conversão Vue.
> Nenhuma fase altera o visual do produto. Todas são refatorações internas.

### Fase 0 — Limpeza de Código Morto ✅ CONCLUÍDA (2026-03-27)

**Esforço:** 1 dia | **Risco:** Zero | **Impacto visual:** Nenhum
**Resultado:** 9.820 linhas removidas, 16 arquivos deletados, 0 imports quebrados

| Ação | Arquivos | Linhas | Como fazer |
|------|----------|--------|-----------|
| Deletar `settings/archived/` | 1 arquivo | 1.905 | `rm -rf` |
| Deletar `talent-funnel-tabs/_archived/` | 3 arquivos | 4.027 | `rm -rf` |
| Deletar `pages/archived/` | 2 arquivos | ~900 | `rm -rf` |
| Deletar `archived/tabs-preview-vaga/` | 2 arquivos (+README) | ~992 | `rm -rf` |
| Deletar `ui/sedPT8vmF` | 1 arquivo | ? | `rm` |
| Total | **9 arquivos** | **~7.800** | |

**Verificação pós-limpeza:** `npm run build` deve passar sem erros. Se algum import quebrar, remover o import (significa que algo já estava importando código morto).

### Fase 1 — Escala Tipográfica ✅ CONCLUÍDA (2026-03-27)

**Esforço:** 2 dias | **Risco:** Baixo | **Impacto visual:** Nenhum (mesmos pixels)
**Resultado:** ~4.500 valores arbitrários eliminados. Zero quebras de build. Zero regressões visuais.

**Tokens implementados (corretos — diferem do plano original):**

| Token | Tamanho | CSS var | Substitui | Usos eliminados |
|-------|---------|---------|-----------|----------------|
| `text-xs` (redefinido) | 11px | `var(--font-size-xs)` | `text-[11px]` | ~2.307 |
| `text-micro` | 10px | `var(--font-size-micro)` | `text-[10px]`, `text-[9px]`, `text-[8px]`, `text-[7px]` | ~2.000+ |
| `text-sm-ui` | 12px | `var(--font-size-sm-ui)` | `text-[12px]` | ~18 |
| `text-base-ui` | 13px | `var(--font-size-base-ui)` | `text-[13px]` | ~186 |

**Correções de plano aplicadas:**
- `text-[11px]` → `text-xs` (não `text-ui` — `text-xs` já era 11px neste projeto)
- `text-[9px]`, `text-[8px]`, `text-[7px]` → `text-micro` (10px mínimo WCAG, nunca `text-tiny`)
- `text-[12px]` → `text-sm-ui` (token novo, não `text-xs` que seria 11px aqui)
- Corrigido bug no `vuetifyMigrationMap`: `text-xs` → `text-caption` (Vuetify) e não `text-body-2`

**Arquivos modificados:** `tailwind.config.ts`, `design-tokens.css`, `design-tokens.ts`, `chat-format.ts` + ~56 componentes

### Fase 2 — Tokenização de Cores (Direção Monocromática)

**Esforço:** 6-7 dias | **Risco:** Baixo-Médio | **Impacto visual:** Mínimo intencional
**Meta:** 150+ cores únicas → **~15 tokens semânticos** (vs. ~28 do plano original)

> **Contexto da revisão (2026-03-27):** Análise profunda do código revelou que 70% da plataforma já é cinza
> (26.337 usos de `gray-*`). A direção Notion/ElevenLabs monocromática é viável e reduz ainda mais a
> paleta, mas LIA não pode ser 100% monocromática por exigência de acessibilidade (WCAG 1.4.1) nos
> estados de status (success/error/warning) e nas etapas do pipeline para escaneabilidade B2B.

#### Decisão Estratégica: O que MANTER vs. ELIMINAR

| Categoria | Instâncias | Decisão | Motivo |
|-----------|-----------|---------|--------|
| Gray scale (6 tons core) | ~26.337 | **MANTER** | Base monocromática |
| Status: red/green/amber | ~4.938 | **MANTER** | WCAG 1.4.1 obrigatório |
| wedo-cyan (LIA/AI only) | ~200 | **MANTER** | Identidade da IA — único accent |
| Pipeline pastéis (17 cores) | ~270 | **CONVERTER** → gray+opacity | Decorativos, não semânticos |
| wedo-cyan decorativo | ~280 | **CONVERTER** → gray | Links, badges, info toasts |
| violet/blue/indigo/rose | ~200 | **ELIMINAR** → gray | Zero valor semântico |
| wedo-orange/purple/magenta | ~100 | **DEPRECAR** | Quase sem uso ativo |
| Chart colors hardcoded | ~40 | **SIMPLIFICAR** → gray escala | Distinção visual, não semântica |
| Email templates | ~125 | **ISENTAR** | HTML inline exige hex |
| Brand terceiros (LinkedIn etc.) | ~50 | **ISENTAR** | Cor institucional imutável |

#### Os 15 Tokens Semânticos Target

```css
/* design-tokens.css — fonte de verdade */

/* GRAY SCALE — 6 tons core (de 11 reduzimos) */
--gray-50:  #F9FAFB;   /* bg page, hover muito sutil */
--gray-200: #E5E7EB;   /* border padrão, divisores */
--gray-400: #9CA3AF;   /* text disabled, placeholder */
--gray-600: #4B5563;   /* text secondary */
--gray-800: #1F2937;   /* text primary forte */
--gray-950: #030712;   /* text máxima ênfase, botão primário */

/* STATUS — 3 semânticas (obrigatório WCAG) */
--status-success: #16A34A;  /* aprovado, contratado */
--status-error:   #DC2626;  /* reprovado, erro */
--status-warning: #D97706;  /* pendente, atenção */

/* BRAND — 1 accent reservado para LIA/AI */
--wedo-cyan:      #60BED1;  /* RESERVADO: ícone LIA, elementos IA únicos */
--wedo-cyan-dark: #4DA8BB;  /* hover state do cyan */

/* CHART — 4 tons para visualização (gray + opacity) */
--chart-1: rgba(3, 7, 18, 1.0);    /* série primária */
--chart-2: rgba(3, 7, 18, 0.6);    /* série secundária */
--chart-3: rgba(3, 7, 18, 0.35);   /* série terciária */
--chart-4: rgba(3, 7, 18, 0.15);   /* série quaternária */
```

---

#### Fase 2A — Bridge Architecture (0,5 dia)

Mesmo padrão da Fase 1: CSS vars como fonte de verdade, `tailwind.config.ts` referencia vars.

**`design-tokens.css` — expandir com gray scale explícito:**
```css
/* Adicionar na seção :root */
--gray-50:  #F9FAFB;
--gray-200: #E5E7EB;
--gray-400: #9CA3AF;
--gray-600: #4B5563;
--gray-800: #1F2937;
--gray-950: #030712;

/* Status semânticos */
--status-success: #16A34A;
--status-error:   #DC2626;
--status-warning: #D97706;
--status-pending: var(--gray-400);   /* Sem nova cor — usa gray + animação */

/* Chart monochromatic */
--chart-1: rgba(3, 7, 18, 1.0);
--chart-2: rgba(3, 7, 18, 0.6);
--chart-3: rgba(3, 7, 18, 0.35);
--chart-4: rgba(3, 7, 18, 0.15);
```

**`tailwind.config.ts` — migrar wedo-* para CSS vars (hoje estão hardcoded):**
```typescript
// ANTES (hardcoded — não sobrevive à migração Vue):
'wedo-cyan': '#60BED1',

// DEPOIS (CSS var — survives framework migration):
'wedo-cyan': 'var(--wedo-cyan)',
'wedo-cyan-dark': 'var(--wedo-cyan-dark)',

// NOVOS tokens de status:
'status-success': 'var(--status-success)',
'status-error':   'var(--status-error)',
'status-warning': 'var(--status-warning)',

// Chart tokens:
'chart-1': 'var(--chart-1)',
'chart-2': 'var(--chart-2)',
'chart-3': 'var(--chart-3)',
'chart-4': 'var(--chart-4)',
```

---

#### Fase 2B — Pipeline Monocromático (1 dia) ← MAIOR GANHO ÚNICO

Arquivo principal: `src/components/ui/status-badge.tsx` (601 linhas, 90 cores hardcoded, 17 tons pastéis)

**Situação atual:** 17 cores pastel únicas para estágios do pipeline (análise confirmou que são decorativas — o kanban já tem fallback cinza e o estágio é identificado por texto+posição).

**Estratégia:** Substituir as 17 cores pastéis por sistema gray + opacity. Manter APENAS verde (contratado) e cinza-claro (reprovado/standby) como estados terminais semânticos.

```typescript
// ANTES — em status-badge.tsx ou recruitment-stages.ts:
const STAGE_COLORS = {
  sourcing:          '#A8CED5',  // cyan-pastel
  triagem:           '#BFA8D5',  // purple-pastel
  long_list:         '#C5D9ED',  // blue-pastel
  short_list:        '#B8C5D0',  // gray-blue
  interview_hr:      '#A8D5B7',  // green-pastel
  technical_test:    '#E8B8B8',  // coral-pink
  // ... 11 mais
  hired:             '#A8D5B7',  // green (duplicate)
  rejected:          '#E5E7EB',  // gray
}

// DEPOIS — sistema gray + opacity:
const STAGE_COLORS = {
  // Estágios ativos — gray com opacidade decrescente pelo funil
  sourcing:          'var(--gray-200)',   // entrada
  triagem:           'var(--gray-200)',
  long_list:         'var(--gray-400)',   // avançando
  short_list:        'var(--gray-400)',
  interview_hr:      'var(--gray-600)',   // em progresso
  technical_test:    'var(--gray-600)',
  english_test:      'var(--gray-600)',
  interview_tech:    'var(--gray-600)',
  interview_manager: 'var(--gray-800)',   // final stretch
  interview_final:   'var(--gray-800)',
  references:        'var(--gray-800)',
  offer:             'var(--gray-950)',   // quase lá
  // Estados terminais — únicos com cor semântica:
  hired:             'var(--status-success)',   // único verde = vitória
  rejected:          'var(--gray-200)',          // faded = encerrado
  offer_declined:    'var(--gray-200)',
  standby:           'var(--gray-200)',
}
```

**Resultado:** 17 cores → 4 valores (gray-200, gray-400-800-950 + status-success). Kanban fica visualmente mais limpo e hierárquico.

---

#### Fase 2C — Hex Hardcoded → Tokens (2 dias)

**Top 20 arquivos com mais hex (cobrem ~70% do problema):**

| Arquivo | Hex count | Ação |
|---------|-----------|------|
| `ui/status-badge.tsx` | 90 | Coberto na Fase 2B |
| `candidate-preview.tsx` | ~63 | find/replace + review manual |
| `jobs-page.tsx` | ~55 | find/replace |
| `dashboards-page.tsx` | ~50 | find/replace |
| `job-kanban-page.tsx` | ~45 | find/replace |
| `charts/interactive-charts.tsx` | ~40 | Substituir COLORS array → chart-1..4 |
| `modals/edit-job-modal.tsx` | ~38 | find/replace |
| `settings/CommunicationHub.tsx` | ~35 | find/replace |
| `pages/indicators-page.tsx` | ~30 | find/replace |
| Demais arquivos (~80) | ~300 total | find/replace em batch |

**Mapa de substituição — Top 15 hex:**

| Hex | → Token Tailwind | Ocorrências |
|-----|-----------------|------------|
| `#374151` | `gray-700` | 120 |
| `#E5E7EB` / `#e5e7eb` | `gray-200` | 116 |
| `#FFFFFF` | `white` | 96 |
| `#6B7280` | `gray-500` | 78 |
| `#111827` | `gray-900` | 75 |
| `#F59E0B` | `status-warning` (não amber-500) | 70 |
| `#D1D5DB` | `gray-300` | 69 |
| `#EF4444` | `status-error` (não red-500) | 48 |
| `#9CA3AF` | `gray-400` | 46 |
| `#F3F4F6` | `gray-100` | 42 |
| `#1a1a1a` | `gray-950` | 38 |
| `#5DA47A` | `status-success` (não wedo-green) | 36 |
| `#EEEEEE` | `gray-200` | 35 |
| `#22C55E` | `status-success` | 33 |
| `#8B5CF6` | `gray-600` (violet tem zero valor semântico aqui) | 28 |

> **Nota sobre violet/blue/indigo/rose:** Estas cores não têm função semântica confirmada no código.
> Converter para gray equivalente em luminosidade. Verificar contexto antes de cada conversão.

---

#### Fase 2D — Restrição do wedo-cyan (1 dia)

**Situação:** 507 usos de cyan. Somente ~200 são semânticos (ícone LIA/Brain, elementos IA).

**Auditoria nos 507 usos — critério de decisão:**
- `text-wedo-cyan` em ícone Brain/AI → **MANTER**
- `text-wedo-cyan` como cor de link → **CONVERTER** para `text-gray-600 underline`
- `bg-wedo-cyan/10` como badge info → **CONVERTER** para `bg-gray-100`
- `text-wedo-cyan-dark` em toast info title → **CONVERTER** para `text-gray-700`
- `border-wedo-cyan` como focus ring → **CONVERTER** para `border-gray-400`
- Cyan em branding/logo da página login → **MANTER**

**Resultado esperado:** 507 → ~200 usos (60% redução). wedo-cyan torna-se exclusivo LIA.

---

#### Fase 2E — Gráficos Monocromáticos (0,5 dia)

**Arquivo:** `src/components/charts/interactive-charts.tsx`

```typescript
// ANTES — 6 hex sem relação com design system:
const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00c49f']

// DEPOIS — 4 tons de cinza com opacidade (tokens definidos na Fase 2A):
const CHART_COLORS = [
  'var(--chart-1)',   // preto puro — série mais importante
  'var(--chart-2)',   // 60% opacidade
  'var(--chart-3)',   // 35% opacidade
  'var(--chart-4)',   // 15% opacidade — série auxiliar
]
```

Adicionar `fill-opacity` como atributo nos SVG para séries adicionais (sem criar nova cor).

---

#### Fase 2F — Validação (0,5 dia)

1. `npm run build` — zero erros
2. Comparação visual das 5 telas críticas: Dashboard, Kanban, Candidato, Chat, Settings
3. Verificar dark mode em cada tela
4. Grep final: `grep -rn "#[0-9A-Fa-f]\{3,6\}" src/ --include="*.tsx" --include="*.ts" --include="*.css"` → deve retornar apenas isentos

---

#### Arquivos Isentos (não migrar)

| Arquivo / Padrão | Motivo |
|-----------------|--------|
| `report-email-templates.tsx` (~125 hex) | HTML inline de email requer hex absoluto |
| LinkedIn `#0A66C2`, Google `#4285F4` | Cores institucionais imutáveis |
| `design-tokens.ts` (62 hex) | É a definição dos tokens — hex aqui é intencional |
| Recharts `stroke`, `fill` em SVG com interpolação dinâmica | API do Recharts requer hex/rgb |

---

#### Resultado esperado da Fase 2 completa

| Métrica | Antes | Depois |
|---------|-------|--------|
| Cores únicas no codebase | 150+ | ~15 tokens semânticos |
| Hex hardcoded em componentes | ~1.607 linhas | ~200 (apenas isentos) |
| Tons do pipeline | 17 pastéis | 4 grays + 1 green (hired) |
| Usos de wedo-cyan | 507 | ~200 (apenas LIA/IA) |
| Acents brand ativos | 4 (cyan, green, orange, purple) | 1 (cyan — LIA exclusivo) |
| Compatibilidade Vuetify | 0% (hex hardcoded) | 100% (CSS vars sobrevivem migração) |

### Fase 3 — Consolidação de Badges e Status

**Esforço:** 2-3 dias | **Risco:** Baixo-Médio | **Impacto visual:** Nenhum

> **Revisão pós-Fase 2 (2026-03-27):** Code review profundo revelou que 2 dos 7 badges são
> órfãos (0 importações), que `field-origin-badge` usa classes Tailwind de cor raw sem tokens,
> e que `badge.tsx` tem 3 valores rgba() hardcoded. Esta fase aplica os tokens semânticos
> da Fase 2 em toda a camada de badges, com estratégia compatível com Vue/Vuetify.

---

#### Diagnóstico Atual (resultado do code review)

| Componente | Linhas | Importações | Estado dos Tokens | Decisão |
|-----------|--------|-------------|-------------------|---------|
| `ui/badge.tsx` | 41 | **295** | 3 rgba() hardcoded | Manter + limpar tokens |
| `ui/status-badge.tsx` | 606 | 2 | Fase 2 aplicada, 5 hex residuais | Manter + limpar hex |
| `ui/setup-alert-badge.tsx` | 207 | 1 (layout.tsx) | 1 hex residual (`#4BA8BA`) | Manter (draggable/fixed — arquitetura ≠ badge) + limpar |
| `job-creation/field-origin-badge.tsx` | 122 | 2 | Tailwind colors raw (bg-blue-100 etc) | Refatorar → tokens DS |
| `wizard/suggestion-badge.tsx` | 146 | **0** | Tailwind colors raw | **Deletar** (órfão) |
| `screening/auto-screening-badge.tsx` | 72 | **0** | Tailwind colors raw | **Deletar** (órfão, só funciona com `source === 'website'`) |
| `ui/chat-status-indicators.tsx` | 339 | 1 (chat-page.tsx) | Já alinhado (gray + wedo-cyan) | Manter separado |

**Resultado real:** 7 → 5 componentes (deletar 2 órfãos, refatorar field-origin)

---

#### Token Contract — Tabela de Mapeamento Canônico

> Regra fundamental: **nenhum badge introduz cor fora desta tabela.** Toda cor nova
> exige atualização aqui antes de ser implementada.

| Variante/Contexto | bg (light) | text (light) | bg (dark) | text (dark) | Semântica |
|-------------------|------------|--------------|-----------|-------------|-----------|
| `default` | `var(--gray-100)` | `var(--gray-800)` | `var(--gray-700)` | `var(--gray-100)` | Neutro genérico |
| `secondary` | `var(--gray-100)` | `var(--gray-600)` | `var(--gray-700)` | `var(--gray-300)` | Secundário |
| `outline` | transparent | `var(--gray-600)` | transparent | `var(--gray-300)` | Contorno sutil |
| `success` | `var(--status-success)/15` | `var(--status-success)` | `var(--status-success)/20` | `var(--status-success)` | Aprovado, ativo |
| `warning` | `var(--status-warning)/15` | `var(--status-warning)` | `var(--status-warning)/20` | `var(--status-warning)` | Atenção, pendente |
| `destructive` | `var(--status-error)/15` | `var(--status-error)` | `var(--status-error)/20` | `var(--status-error)` | Erro, rejeitado |
| `info` (LIA/IA only) | `var(--wedo-cyan)/15` | `var(--wedo-cyan-dark)` | `var(--wedo-cyan)/20` | `var(--wedo-cyan)` | Contexto IA — reservado |
| `lilac` | `var(--wedo-purple)/15` | `var(--wedo-purple)` | `var(--wedo-purple)/20` | `var(--wedo-purple)` | Benchmark, especulativo |
| Pipeline early (sourcing/screening) | `var(--gray-200)` | `var(--gray-600)` | `var(--gray-600)` | `var(--gray-200)` | Funil inicial |
| Pipeline mid (long_list → tests) | `var(--gray-300)`–`var(--gray-400)` | `var(--gray-800)` | — | — | Em triagem |
| Pipeline advanced (interviews) | `var(--gray-500)`–`var(--gray-600)` | `#FFFFFF` | — | — | Avançando |
| Pipeline final (offer) | `var(--gray-800)` | `#FFFFFF` | — | — | Decisão |
| Pipeline hired | `var(--status-success)` | `#FFFFFF` | — | — | Contratado |
| Pipeline rejected/declined | `var(--gray-200)` | `var(--gray-600)` | — | — | Terminal |

> `#FFFFFF` nas linhas de pipeline advanced/final/hired é semântico: texto branco
> sobre fundo escuro não muda com tema — não é um token, é uma constante visual.

---

#### Mapeamento Vue/Vuetify

> Cada variante de badge deve ter um mapeamento explícito para Vue/Vuetify.
> CSS vars definidos na Fase 2 sobrevivem à migração de framework.

| badge.tsx variant | Vuetify component | Props Vuetify |
|-------------------|------------------|---------------|
| `default` | `v-chip` | `:color="undefined"` (uses default) |
| `secondary` | `v-chip` | `variant="tonal"` |
| `outline` | `v-chip` | `variant="outlined"` |
| `success` | `v-chip` | `color="success"` (mapear p/ status-success token) |
| `warning` | `v-chip` | `color="warning"` (mapear p/ status-warning token) |
| `destructive` | `v-chip` | `color="error"` (mapear p/ status-error token) |
| `info` | `v-chip` | `color="info"` (mapear p/ wedo-cyan token) |
| `lilac` | `v-chip` | `:color="'var(--wedo-purple)'"` |
| StatusBadge pipeline | `v-chip` | `:style="{ backgroundColor: stageColor }"` |
| FieldOriginBadge | `v-chip` | `:prepend-icon` + `:color` por origin |
| SetupAlertBadge | `v-fab` / `v-sheet` | Componente flutuante — sem equivalente direto em chip |
| ChatStatusIndicators | `v-progress-linear` + `v-alert` | Padrão de feedback de IA |

---

#### Fase 3A — Limpeza de Tokens no `badge.tsx` (½ dia)

**Problema:** 3 valores `rgba()` hardcoded nas variantes success, warning/danger, lilac.

**Ação:** Substituir por CSS vars com opacidade.

```typescript
// ANTES
'success': 'bg-[rgba(123,194,154,0.15)] text-wedo-green ...',
'warning': 'bg-[rgba(232,168,124,0.15)] text-wedo-orange ...',
'lilac':   'bg-[rgba(201,160,220,0.15)] text-wedo-purple ...',

// DEPOIS — usando tokens semânticos da Fase 2
'success': 'bg-wedo-green/15 text-wedo-green dark:bg-wedo-green/20 ...',
'warning': 'bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/20 ...',
'danger':  'bg-status-error/15 text-status-error dark:bg-status-error/20 ...',
'lilac':   'bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/20 ...',
```

> Nota: `bg-wedo-green/15` requer hex no tailwind.config.ts (não CSS var) — já existe.

---

#### Fase 3B — Limpeza de Hex Residuais no `status-badge.tsx` (½ dia)

**5 hex residuais identificados no code review:**

| Hex | Localização | Substituição |
|-----|-------------|-------------|
| `#374151` | STAGE_PASTEL_COLORS_DARK (gray-600 dark) | `var(--gray-600)` |
| `#15803D` | hired dark mode icon | `var(--status-success)` |
| `#FFFFFF` | text/icon em variantes dark/scheduled/hired | Manter (semântico: branco sobre escuro) |
| `#E3DADC` | fallback pastel color default | `var(--gray-200)` |
| `#4A3D40` | fallback pastel dark color | `var(--gray-600)` |

---

#### Fase 3C — Refatorar `field-origin-badge.tsx` → Tokens DS (1 dia)

**Problema:** Usa Tailwind color classes raw (`bg-blue-100 text-blue-700`) sem relação com design system.

**Mapeamento de origens → tokens:**

| Origem | Antes | Depois | Justificativa |
|--------|-------|--------|---------------|
| `detected` (IA) | `bg-blue-100 text-blue-700` | `bg-wedo-cyan/15 text-wedo-cyan-dark` | Contexto IA = wedo-cyan (token info) |
| `default` (empresa) | `bg-green-100 text-green-700` | `bg-wedo-green/15 text-wedo-green` | Configuração padrão = verde positivo |
| `manual` (humano) | `bg-gray-100 text-gray-700` | `bg-[var(--gray-200)] text-[var(--gray-600)]` | Manual = neutro gray |
| `suggested` (similar) | `bg-yellow-100 text-yellow-700` | `bg-status-warning/15 text-status-warning` | Sugestão = atenção (warning) |
| `benchmark` (mercado) | `bg-purple-100 text-purple-700` | `bg-wedo-purple/15 text-wedo-purple` | Especulativo = lilac |

**Estrutura após refator:** manter toda a lógica de origins, substituir apenas as strings de classes de cor.

---

#### Fase 3D — Limpar `setup-alert-badge.tsx` (¼ dia)

**1 hex residual:**
- `#4BA8BA` → `var(--wedo-cyan)` (progresso 50-80%)

**Manter:** toda a lógica draggable, localStorage, fetch, progress bar — arquitetura específica que não tem equivalente em `badge.tsx`.

---

#### Fase 3E — Deletar Órfãos (¼ dia)

**Verificar antes de deletar** (grep por usos dinâmicos):
```bash
grep -r "SuggestionBadge\|AutoScreeningBadge\|suggestion-badge\|auto-screening-badge" src/ --include="*.tsx" --include="*.ts"
```

Se confirmado 0 usos:
- Deletar `src/components/wizard/suggestion-badge.tsx` (146 linhas)
- Deletar `src/components/screening/auto-screening-badge.tsx` (72 linhas)
- Total: **218 linhas removidas**

---

#### Resultado Esperado da Fase 3

| Métrica | Antes | Depois |
|---------|-------|--------|
| Componentes de badge | 7 | **5** (deletar 2 órfãos) |
| Hex/rgba hardcoded em badges | ~11 | **~2** (só `#FFFFFF` semântico) |
| field-origin usando tokens DS | ✗ | ✓ |
| Token Contract documentado | ✗ | ✓ |
| Vuetify migration map | ✗ | ✓ |
| Linhas de código eliminadas | — | ~218 (órfãos) |
| Arquivos que precisam ser alterados | — | 4 (badge, status-badge, field-origin, setup-alert) |

### Fase 4 — Split de Componentes Gigantes

**Esforço:** 3-4 semanas | **Risco:** Alto | **Impacto visual:** Nenhum

> Esta é a fase mais complexa. Requer testes extensivos após cada split.
> Recomendação: fazer 1 componente por sprint, testar completamente antes de avançar.

**Sprint 1 — `expanded-chat-modal.tsx` (11.824 linhas)**

| Sub-componente proposto | Responsabilidade | Linhas estimadas |
|------------------------|------------------|-----------------|
| `ExpandedChatContainer` | Layout, state global, context | ~800 |
| `ChatMessageList` | Renderização de mensagens | ~1.500 |
| `ChatInputBar` | Input, upload, voz | ~800 |
| `WizardStagePanel` | Painel lateral do wizard | ~1.200 |
| `ToolExecutionResults` | Cards de resultado de tools | ~600 |
| `ChatStateReducer` | Reducer de estado do chat | ~500 |
| `FieldSyncManager` | Sync de campos wizard↔chat | ~400 |
| `JobPreviewPanel` | Preview da vaga em criação | ~800 |
| `ChatMessageTypes` | Tipos e interfaces TypeScript | ~200 |
| Restante no modal principal | Orchestração | ~5.000 |

**Sprint 2 — Pages gigantes (28.752 linhas total)**

| Arquivo | Linhas | Split proposto |
|---------|--------|---------------|
| `job-kanban-page` | 10.377 | KanbanHeader, KanbanBoard, KanbanColumn, CandidateKanbanCard, BulkActionsBar, StageConfig, KanbanAnalytics |
| `candidates-page` | 10.329 | CandidateTableView, FilterPanel, BulkActions, CandidatePreviewPanel, SearchBar, Pagination |
| `jobs-page` | 8.046 | JobsTableView, JobCardView, JobFilters, JobStats, BulkActions |

**Sprint 3 — Candidatos (9.227 linhas)**

| Arquivo | Linhas | Split proposto |
|---------|--------|---------------|
| `candidate-preview` | 6.723 | ProfileHeader, ExperienceTimeline, SkillsSection, WSISection, NotesSection, ActionsBar, PreviewTabs |
| `candidate-page` | 2.504 | CandidateProfileSections, CandidateTimeline, CandidateActions |

**Sprint 4 — Search e Settings (14.992 linhas)**

| Arquivo | Linhas | Split proposto |
|---------|--------|---------------|
| `smart-search-input` | 5.475 | SearchBar, FilterChips, SuggestionsList, BooleanBuilder, SearchResults |
| `CompanyTeamHub` | 5.235 | TeamTable, InviteModal, RoleManager, Permissions, ActivityLog |
| `expandable-ai-prompt` | 4.308 | PromptInput, SuggestionDock, AttachmentBar, ActionChips |

### Fase 5 — Padronização de Dimensões

**Esforço:** 3-5 dias | **Risco:** Médio | **Impacto visual:** Mínimo

**Passo 1 — Criar tokens de layout no `tailwind.config.ts`:**

```typescript
extend: {
  width: {
    'panel-sm': '300px',
    'panel-md': '350px',
    'panel-lg': '400px',
    'panel-xl': '500px',
    'sidebar-content': '200px',
  },
  height: {
    'chart': '200px',
    'panel-md': '300px',
    'panel-lg': '400px',
    'card-lg': '180px',
  },
}
```

**Passo 2 — Substituir valores com equivalente Tailwind exato:**

| De | Para | Usos |
|----|------|------|
| `w-[80px]` | `w-20` | 7 |
| `h-[56px]` | `h-14` | 5 |
| `h-[80px]` | `h-20` | 5 |

**Passo 3 — Converter inline styles para Tailwind:**
- Focar nos 249 arquivos com `style=`
- Priorizar: componentes com dark mode, componentes de layout, componentes da ui/

---

## 19. Impacto na Conversão para Vue/Vuetify

Após completar as Fases 0-3 (~2 semanas), o benefício para conversão Vue é substancial:

| Antes da otimização | Depois da otimização |
|---------------------|---------------------|
| 298 cores hardcoded — cada uma precisa de tradução manual | Tokens nomeados — mapear token React → token Vuetify automaticamente |
| `text-[11px]` espalhado — sem semântica, impossível mapear | `text-ui` — mapear para `.wedo-label { font-size: 0.6875rem }` no Vue |
| 37 monólitos de 1.000-11.000 linhas — impossível converter | Sub-componentes de 200-800 linhas — conversão componente por componente |
| 7 tipos de badge — qual é o canônico? | 3 tipos claros — traduzir 1:1 para Vue |

**Fórmula de esforço para conversão Vue:**
- Sem otimização: ~465 componentes × análise individual = impraticável
- Com Fases 0-3: ~450 componentes tokenizados × conversão mecânica = viável
- Com Fases 0-5: ~150 componentes menores tokenizados × conversão automatizável = ótimo

---

## 20. Tabela-Resumo do Plano

| Fase | O que faz | Resultado | Impacto visual | Risco | Esforço | Benefício Vue |
|------|----------|-----------|---------------|-------|---------|--------------|
| 0 — Limpeza ✅ | Remove código morto | 9.820 linhas removidas | Nenhum | Zero | 1 dia ✅ | Reduz ruído |
| 1 — Tipografia ✅ | text-[Xpx] → 4 tokens com CSS vars | ~4.500 valores eliminados | Nenhum | Baixo | 2 dias ✅ | Mapeamento 1:1 para Vuetify |
| 2 — Cores | 150+ hex → 15 tokens semânticos (direção monocromática) | Pipeline: 17 pastéis→4 grays; cyan: 507→200 usos | Mínimo intencional | Baixo-Médio | 6-7 dias | CSS vars sobrevivem migração Vue |
| 3 — Badges | 7 → 3 componentes | Tokens + badge.tsx como base | Nenhum | Médio | 2-3 dias | Decide componente canônico |
| 4 — Split | 37 → ~150 sub-componentes | Monólitos < 800 linhas | Nenhum | Alto | 3-4 semanas | Conversão componente a componente |
| 5 — Dimensões | px → tokens de layout | ~5.400 valores arbitrários | Mínimo | Médio | 3-5 dias | Tokens compartilhados |
| **Total** | | **~138.700** | **Zero** | | **~6-7 semanas** | **Conversão viável** |
