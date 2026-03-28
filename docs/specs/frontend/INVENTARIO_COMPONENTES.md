# Inventário Completo de Componentes — Plataforma LIA (React)

> **Última atualização:** 2026-03-28 (Sprint 4.6 — Monolith Split: 13 componentes extraídos de 4 monolitos, -6.693L)
> **Arquitetura:** Bridge Architecture — 3 camadas de abstração (CSS vars → framework config → componentes) — ver Seção 0
> **Componentes:** 569 em 38 diretórios (556 anteriores + 13 novos do Sprint 4.6 em 4 subdirs — novo subdir `candidate-preview/`)
> **Hooks:** 120 custom hooks (93 em `src/hooks/` + 27 em subdiretórios de componentes)
> **Infraestrutura:** 5 contexts, 17 arquivos de types/config, 13 lib utilities
> **Rotas:** 90 page routes + 5 layouts + 424 API endpoints
> **CSS:** 242 variáveis, 29 keyframes, 200+ classes customizadas, 169 ícones Lucide
> **Localização:** `plataforma-lia/src/`
> **Stack:** React 19 + Next.js 15 + Tailwind CSS + shadcn/ui (Radix UI)

---

## 0. Bridge Architecture — Princípio Fundacional

> **Status:** Em implementação ativa (Fase 1 concluída, Fases 2-5 pendentes)
> **Última atualização:** 2026-03-27

### 0.1 O Problema

A Plataforma LIA nasceu como aplicação React + Tailwind com decisões de estilo tomadas diretamente nos componentes: cores hex hardcoded, tamanhos arbitrários (`text-[11px]`), espaçamentos inline. Isso criou 3 problemas concretos:

1. **Inconsistência visual** — 298 cores únicas, 4.765 valores arbitrários Tailwind, 249 arquivos com inline styles
2. **Manutenção cara** — uma mudança de cor exige tocar dezenas de arquivos
3. **Migração impossível** — cada valor hardcoded é um ponto de reescrita manual na conversão para Vue/Vuetify

### 0.2 A Solução: 3 Camadas de Abstração

A Bridge Architecture resolve isso com 3 camadas onde **cada uma só conhece a camada imediatamente abaixo:**

```
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 3 — Componentes (React hoje / Vue amanhã)           │
│  Consomem apenas classes semânticas do framework            │
│  Ex: className="text-xs text-status-success bg-wedo-cyan"  │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 2 — Framework Config (tailwind.config.ts)           │
│  Mapeia nomes semânticos para CSS vars                      │
│  Ex: 'text-xs' → var(--font-size-xs)                       │
│  Ex: 'wedo-cyan' → var(--wedo-cyan)                        │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 1 — CSS Variables (design-tokens.css)               │
│  Fonte única de verdade — 181 variáveis definidas           │
│  Ex: --font-size-xs: 11px; --wedo-cyan: #60BED1            │
│  Portável entre frameworks: React, Vue, Angular, vanilla    │
└─────────────────────────────────────────────────────────────┘
```

**Princípio:** Nenhum componente deve referenciar diretamente um valor de cor, tamanho ou espaçamento. Tudo passa pela bridge.

### 0.3 As 6 Dimensões de Padronização

A Bridge Architecture não se limita a tokens CSS. Todo trabalho de refatoração do front segue **6 dimensões** que determinam como cada sprint é planejado e executado:

| # | Dimensão | O que governa | Onde se aplica |
|---|----------|---------------|----------------|
| 1 | **Bridge Architecture (CSS vars)** | Tokens visuais — cores, tipografia, espaçamento, sombras | Sprints de tokenização (ex: 4.1.5). Hooks e lógica de estado **não tocam CSS** — a bridge já cuida |
| 2 | **Monochromatic Design System** | Paleta Notion/ElevenLabs — preto + wedo-cyan como accent | Componentes com JSX/UI. Sprints de extração de UI (ex: 4.3). Não afeta hooks TS puros |
| 3 | **Token Inventory (status-*, chart-*, gray-*)** | Vocabulário semântico: `status-error`, `wedo-green`, `chart-1` | Idem — aplica-se quando se cria/modifica componentes visuais |
| 4 | **WeDOTalent Color Standardization** | Consolidação das 298 cores únicas em ~30 tokens canônicos | Sprints de cores (Fase 2). Hooks são TS puro — não afetados |
| 5 | **Vue Migration Prep** | Estrutura de código compatível com Pinia/Vue 3 | **Crítico em hooks:** padrão `{ state, actions }` compatível com Pinia stores. Sem `useContext`, sem HOCs, sem `cloneElement` |
| 6 | **Separação de Concerns** | Lógica de estado separada de apresentação | Sprints de extração de hooks (ex: 4.2). Objetivo: cada componente com estado zero — tudo em hooks reutilizáveis |

**Como as dimensões interagem por sprint:**

```
Sprint 4.1.5 (Tokenização)     → Dimensões 1, 2, 3, 4 (CSS vars, paleta, tokens, cores)
Sprint 4.2   (Extração hooks)  → Dimensões 5, 6 (Vue prep, separação de concerns)
Sprint 4.3   (Extração UI)     → Dimensões 1, 2, 3, 4, 5 (tokens + componentes Vue-ready)
Sprint 4.4+  (Integração)      → Todas as 6 dimensões auditadas
```

> **Regra:** Nenhum sprint modifica código sem validar qual subconjunto das 6 dimensões se aplica.

### 0.4 Impacto: Sem Bridge vs Com Bridge

| Cenário | Sem Bridge | Com Bridge |
|---------|-----------|------------|
| Mudar cor principal | Editar 54+ arquivos | Editar 1 variável CSS |
| Adicionar dark mode | Reescrever cada componente | Override de variáveis por tema |
| Migrar React → Vue | Reescrever 4.765 valores | Manter camada 1, substituir camada 2 |
| Ajustar tipografia | Encontrar 1.287 ocorrências | Mudar 4 tokens |
| Auditar consistência | Impossível sem varredura | Grep em design-tokens.css |

### 0.5 Arquivos da Bridge

| Camada | Arquivo | Linhas | Papel |
|--------|---------|--------|-------|
| 1 | `src/styles/design-tokens.css` | 820 | Variáveis CSS — fonte única de verdade |
| 1 | `src/app/globals.css` | 1.477 | Variáveis compostas, keyframes, classes utilitárias |
| 2 | `tailwind.config.ts` | ~200 | Mapeia tokens para classes Tailwind |
| 2→3 | `src/lib/design-tokens.ts` | 644 | Tokens em TypeScript + mapeamento Tailwind→Vuetify |
| 2→3 | `src/lib/theme-colors.ts` | ~150 | Temas por página (6 variantes) |

### 0.6 O que Já Está Implementado

**Fase 0 — Limpeza (concluída 2026-03-27):**
- 16 arquivos de dead code removidos (9.820 linhas)
- Componentes: 465 → 460

**Fase 1 — Tipografia (concluída 2026-03-27):**
- 4 tokens customizados criados: `text-xs` (11px), `text-micro` (10px), `text-sm-ui` (12px), `text-base-ui` (13px)
- Camada 1: variáveis em `design-tokens.css` (`--font-size-xs`, `--font-size-micro`, etc.)
- Camada 2: `tailwind.config.ts` referencia as variáveis (`fontSize: { 'xs': ['var(--font-size-xs)', ...] }`)
- Camada 3: componentes usam classes normais (`text-xs`) que agora mapeiam para CSS vars
- ~4.500 valores arbitrários de tipografia eliminados

**Infraestrutura de Migração Vue:**
- `design-tokens.ts` contém `tailwindToVuetify` com mapeamentos completos de cores, tipografia, espaçamento, border-radius, sombras e layout — pronto para consumo por scripts de conversão automatizada

### 0.7 O que Falta (Fases 2-5)

> **Status:** Em implementação ativa (Fases 1-4 concluídas, Fases 5+ pendentes)

| Fase | Escopo | Impacto | Status |
|------|--------|---------|--------|
| 2 | Cores — tokenizar 298 hex hardcoded | Eliminar 54 arquivos com cores fora do DS | Pendente |
| 3 | Badges & Status — unificar 7 implementações | Componente único `<StatusBadge>` | Pendente |
| 4 | Giant Components — refatorar 37 arquivos >1.000 linhas | Reduzir 118.037 → ~60.000 linhas | ✅ Sprint 4.6: 13 componentes extraídos de 4 monolitos (-6.693L total) |
| 5 | Modals & Inline Styles — padronizar | 154 arquivos com modals, 249 com inline styles | Pendente |

> **Detalhamento completo das fases:** seções 29-32 deste documento.

### 0.8 Regras Para Novos Desenvolvimentos

Qualquer código novo ou modificado **deve** seguir as dimensões aplicáveis:

**Componentes com UI (JSX/TSX) — Dimensões 1-5:**

```
✅ CORRETO — Usa token semântico:
  className="text-xs text-status-success bg-wedo-cyan"

❌ ERRADO — Valor hardcoded:
  className="text-[11px] text-green-600"
  style={{ color: '#60BED1', fontSize: '11px' }}
```

**Hooks e lógica de estado (TS puro) — Dimensões 5-6:**

```
✅ CORRETO — Padrão { state, actions } compatível com Pinia:
  export function useJobFilters() {
    const [filters, setFilters] = useState<JobFilters>(defaults)
    const actions = { setStatus, clearAll, applyPreset }
    return { ...filters, ...actions }        // → Pinia store shape
  }

❌ ERRADO — Acoplado a React internals:
  // useContext direto no hook de estado (não traduz para Pinia)
  // cloneElement / HOCs (não existem em Vue 3)
  // Estado misturado com renderização JSX
```

**Checklist por tipo de mudança:**

| Tipo de mudança | Dimensões obrigatórias |
|-----------------|----------------------|
| Novo componente UI | 1 (tokens CSS), 2 (monocromático), 3 (vocabulário semântico), 5 (Vue-ready) |
| Novo hook de estado | 5 (padrão Pinia), 6 (concerns separados) |
| Modificar cores | 1 (via design-tokens.css), 4 (consolidação WeDOTalent) |
| Novo modal/dialog | 1 (tokens), 2 (palette), 5 (composable pattern) |
| Refatorar componente gigante | Todas as 6 dimensões |

> **Esta seção é um documento vivo.** Será atualizada conforme as fases avançam e a arquitetura evolui.

---

## 1. UI Base (`ui/`) — 64 componentes

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
| 13 | `expanded-chat-modal` | 11228 | Modal principal do chat expandido (maior componente) |
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
| 6 | `candidate-preview` | 5994 | Preview expandido (2º maior componente) — subdir `candidate-preview/` com FilePreviewModal (548L) e LiaChatModal (316L) extraídos no Sprint 4.6 |
| 7 | `cv/cv-preview` | 641 | Preview de currículo |
| 8 | `cv/cv-upload-modal` | 473 | Modal de upload de CV |
| 9 | `triagem/pre-screening-config-drawer` | 345 | Drawer de configuração de triagem |
| 10 | `triagem/screening-interview-card` | 356 | Card de entrevista de triagem |
| 11 | `triagem/screening-pipeline-stats` | 252 | Estatísticas do pipeline de triagem |
| 12 | `triagem/screening-report-export` | 429 | Exportação de relatório de triagem |
| 13 | `triagem/triagem-detail-panel` | 764 | Painel de detalhe da triagem |
| 14 | `triagem/triagem-table` | 577 | Tabela de triagem |
| 15 | `triagem-details-modal` | 1194 | Modal de detalhes da triagem |

---

## 5. Search & Sourcing (`search/`) — 40 componentes

Busca inteligente e sourcing de candidatos. Inclui filtros avançados, presets geográficos e modais de configuração.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `search/advanced-filters-modal` | 3282 | Modal de filtros avançados (5º maior componente) |
| 2 | `search/advanced-search` | 333 | Busca avançada com múltiplos critérios |
| 3 | `search/ArchetypesList` | 274 | Lista de arquétipos de candidato |
| 4 | `search/candidate-detail-sidebar` | 455 | Sidebar de detalhe do candidato nos resultados |
| 5 | `search/CompanyFilterInput` | 566 | Input de filtro por empresa |
| 6 | `search/CompanyHQLocationsInput` | 328 | Input de localização de HQ da empresa |
| 7 | `search/CompanyPresetsModal` | 552 | Modal de presets de empresas |
| 8 | `search/CompanyTagsInput` | 454 | Input de tags de empresa |
| 9 | `search/credit-confirmation-dialog` | 153 | Dialog de confirmação de uso de créditos |
| 10 | `search/credit-cost-display` | 199 | Display de custo em créditos |
| 11 | `search/DegreeRequirementsInput` | 166 | Input de requisitos de grau acadêmico |
| 12 | `search/ExcludedCompaniesInput` | 363 | Input de empresas excluídas |
| 13 | `search/ExcludedUniversitiesInput` | 280 | Input de universidades excluídas |
| 14 | `search/ExpertiseAreasInput` | 331 | Input de áreas de expertise |
| 15 | `search/FieldsOfStudyInput` | 590 | Input de campos de estudo |
| 16 | `search/filter-autocomplete` | 360 | Autocomplete genérico de filtros |
| 17 | `search/FundingStagesInput` | 90 | Input de estágio de funding da empresa |
| 18 | `search/GraduationYearInput` | 99 | Input de ano de graduação |
| 19 | `search/IndustryFilterInput` | 466 | Filtro por indústria |
| 20 | `search/IndustrySingleSelect` | 269 | Select único de indústria |
| 21 | `search/LanguageFilterInput` | 333 | Filtro de idiomas |
| 22 | `search/LocationFilterInput` | 410 | Filtro de localização |
| 23 | `search/LocationPresetsModal` | 457 | Modal de presets de localização |
| 24 | `search/PastLocationsInput` | 341 | Input de localizações anteriores |
| 25 | `search/QualificationBadge` | 175 | Badge de qualificação do candidato |
| 26 | `search/RadiusDropdown` | 112 | Dropdown de raio geográfico |
| 27 | `search/save-archetype-modal` | 320 | Modal para salvar arquétipo |
| 28 | `search/SearchFeedbackButtons` | 103 | Botões de feedback de resultado |
| 29 | `search/search-preview-card` | 272 | Card de preview de resultado |
| 30 | `search/SearchQualityPanel` | 96 | Painel de qualidade da busca |
| 31 | `search/search-results-card` | 497 | Card de resultado de busca |
| 32 | `search/SearchSourceSelector` | 155 | Seletor de fonte de busca |
| 33 | `search/SimilarProfilesInput` | 246 | Input de perfis similares |
| 34 | `search/SkillsFilterInput` | 370 | Filtro de skills |
| 35 | `search/smart-search-input` | 5475 | Input de busca inteligente (3º maior componente) |
| 36 | `search/TimezoneDropdown` | 170 | Dropdown de timezone |
| 37 | `search/UniversitiesFilterInput` | 460 | Filtro de universidades |
| 38 | `search/UniversityLocationsInput` | 276 | Input de localização de universidades |
| 39 | `search/UniversityPresetsModal` | 729 | Modal de presets de universidades |
| 40 | `search/expandable-ai-prompt.types` | 149 | Types do prompt expansível (TS) |

---

## 6. Pipeline & Kanban (`kanban/`, `pipeline/`, `jobs/`) — 30 arquivos (11 componentes + 6 hooks + 5 utils + 4 types/config + 4 barrel)

Gestão visual do pipeline de recrutamento. Estrutura modular com hooks, utils e types dedicados.

**Componentes (`kanban/components/`):**

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `kanban/components/CandidateBadges` | 88 | Badges do candidato no kanban |
| 2 | `kanban/components/CandidateCard` | 428 | Card do candidato no kanban |
| 3 | `kanban/components/CandidateTableRow` | 349 | Row de candidato em modo tabela |
| 4 | `kanban/components/ColumnContextMenu` | 260 | Menu de contexto da coluna |
| 5 | `kanban/components/KanbanBoard` | 133 | Board principal do kanban |
| 6 | `kanban/components/KanbanColumn` | 209 | Coluna do kanban com drag & drop |
| 7 | `kanban/components/OverrideApproveButton` | 117 | Botão de aprovação de override |
| 8 | `kanban/components/SaturationBadge` | 266 | Badge de saturação de etapa |
| 9 | `kanban/components/TransitionChatPanel` | 488 | Painel de chat para transição de etapa |
| 10 | `kanban/components/UniversalTransitionModal` | 845 | Modal universal de transição |

**Hooks (`kanban/hooks/`):**

| # | Hook | Linhas | Função |
|---|------|--------|--------|
| 1 | `use-candidate-selection` | 85 | Seleção de candidatos no kanban |
| 2 | `use-column-config` | 136 | Configuração de colunas |
| 3 | `use-drag-drop` | 156 | Drag & drop entre colunas |
| 4 | `use-filters-persistence` | 140 | Persistência de filtros |
| 5 | `use-kanban-filters` | 88 | Filtros do kanban |
| 6 | `use-universal-transition` | 131 | Lógica de transição entre etapas |

**Utils (`kanban/utils/`):**

| # | Util | Linhas | Função |
|---|------|--------|--------|
| 1 | `action-matrix` | 130 | Matriz de ações por estágio |
| 2 | `badge-utils` | 146 | Utilitários de badges |
| 3 | `filter-utils` | 60 | Utilitários de filtros |
| 4 | `stage-utils` | 217 | Utilitários de estágios |
| 5 | `status-utils` | 131 | Utilitários de status |

**Types & Config:**

| # | Arquivo | Linhas | Função |
|---|---------|--------|--------|
| 1 | `kanban/types` | 118 | Tipos do kanban |
| 2 | `kanban/constants` | 122 | Constantes (estágios, cores) |
| 3 | `kanban/mock/candidates` | 1559 | Dados mock de candidatos |
| 4 | `kanban/mock/data-generators` | 255 | Geradores de dados mock |

**Pipeline & Jobs:**

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `pipeline/pipeline-analytics` | 619 | Analytics do pipeline |
| 2 | `pipeline/pipeline-comparison` | 457 | Comparação de pipelines |
| 3 | `pipeline/pipeline-configuration` | 590 | Configuração de etapas |
| 4 | `pipeline/pipeline-stage-insights` | 423 | Insights por etapa |
| 5 | `jobs/job-card-enhanced` | 365 | Card de vaga aprimorado |
| 6 | `jobs/jobs-header` | 202 | Header da lista de vagas |
| 7 | `jobs/jobs-page` | 423 | Página principal de vagas |
| 8 | `jobs/jobs-stats` | 205 | Estatísticas de vagas |
| 9 | `jobs/jobs-table` | 316 | Tabela de vagas |
| 10 | `jobs/tab-content-with-actions` | 111 | Tab com ações contextuais |

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
| 10 | `ml-insights-card` | 181 | Card de insights ML |
| 11 | `lia-metrics-dashboard` | 897 | Dashboard de métricas LIA |

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

## 13. Talent Funnel (`talent-funnel-tabs/`) — 4 componentes

> **Nota:** Fase 0 removeu 3 componentes arquivados (`mapping-tab`, `personas-tab`, `pipelines-tab`) — 4.027 linhas de código morto eliminadas.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `talent-funnel-tabs/favorites-tab` | 553 | Tab de favoritos |
| 2 | `talent-funnel-tabs/history-tab` | 394 | Tab de histórico |
| 3 | `talent-funnel-tabs/lists-tab` | 924 | Tab de listas de candidatos |
| 4 | `talent-funnel-tabs/saved-searches-tab` | 633 | Tab de buscas salvas |

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

## 16. Componentes Standalone (raiz) — 62 componentes

Componentes na raiz de `src/components/` sem subdiretório dedicado.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `activity-feed` | 506 | Feed de atividades |
| 2 | `ai-search-toggle` | 471 | Toggle de busca IA |
| 3 | `batch-approval-modal` | 946 | Modal de aprovação em lote |
| 4 | `big-five-modal` | 545 | Modal Big Five personality |
| 5 | `bulk-actions-bar` | 728 | Barra de ações em massa |
| 6 | `calibration-card` | 328 | Card de calibração |
| 7 | `candidate-comparison` | 590 | Comparação lado a lado de candidatos |
| 8 | `candidate-decision-flow-modal` | 524 | Modal de fluxo de decisão |
| 9 | `candidate-modal` | 655 | Modal completo do candidato |
| 10 | `candidate-page` | 2504 | Página completa do candidato |
| 11 | `candidate-preview` | 5994 | Preview expandido — era 6.723, -729L Sprint 4.6 |
| 12 | `column-configuration-modal` | 346 | Modal de configuração de colunas |
| 13 | `company-screening-settings` | 507 | Config de triagem da empresa |
| 14 | `contextual-actions-banner` | 172 | Banner de ações contextuais |
| 15 | `daily-briefing-card` | 564 | Card de briefing diário |
| 16 | `dashboard-app` | 187 | App principal do dashboard |
| 17 | `disc-assessment-modal` | 557 | Modal de assessment DISC |
| 18 | `events-section` | 440 | Seção de eventos |
| 19 | `expandable-ai-prompt` | 4308 | Prompt expansível da IA (5º maior) |
| 20 | `expanded-chat-modal` | 11228 | Modal do chat expandido (maior componente) |
| 21 | `experience-highlight-card` | 247 | Card de destaque de experiência |
| 22 | `export-tools` | 325 | Ferramentas de exportação |
| 23 | `fairness-warning-banner` | 49 | Banner de aviso de fairness/viés |
| 24 | `global-search-modal` | 482 | Modal de busca global |
| 25 | `intelligence-notifications` | 404 | Notificações inteligentes |
| 26 | `interviews-section` | 202 | Seção de entrevistas |
| 27 | `job-actions-bar` | 116 | Barra de ações de vaga |
| 28 | `job-report-modal` | 556 | Modal de relatório de vaga |
| 29 | `lia-activity-feed` | 448 | Feed de atividades da LIA |
| 30 | `lia-expanded-prompt` | 199 | Prompt expandido da LIA |
| 31 | `lia-metrics-chart` | 181 | Gráfico de métricas LIA |
| 32 | `lia-metrics-dashboard` | 897 | Dashboard de métricas LIA |
| 33 | `lia-performance-indicators` | 178 | Indicadores de performance LIA |
| 34 | `lia-processing-card` | 426 | Card de processamento LIA |
| 35 | `lia-score-card` | 140 | Scorecard LIA |
| 36 | `lia-screening-dialogue` | 905 | Diálogo de triagem LIA |
| 37 | `lia-screening-guide` | 1131 | Guia de triagem LIA |
| 38 | `lia-suggestion-cards` | 161 | Cards de sugestão da LIA |
| 39 | `lia-tips-modal` | 447 | Modal de dicas LIA |
| 40 | `login-page` | 458 | Página de login (componente) |
| 41 | `ml-insights-card` | 181 | Card de insights ML |
| 42 | `notification-system` | 449 | Sistema de notificações |
| 43 | `page-transition` | 45 | Transição entre páginas |
| 44 | `presentation-mode` | 422 | Modo apresentação |
| 45 | `proactive-insight-card` | 364 | Card de insight proativo |
| 46 | `quick-actions-modals` | 2076 | Modais de ações rápidas |
| 47 | `quick-view-modal` | 393 | Modal de visualização rápida |
| 48 | `react-thinking-stream` | 53 | Stream de pensamento (React) |
| 49 | `regional-analysis` | 514 | Análise regional |
| 50 | `reveal-credits-modal` | 124 | Modal de créditos de reveal |
| 51 | `rubric-evaluation-card` | 368 | Card de avaliação por rubrica |
| 52 | `rubric-evaluation-modal` | 872 | Modal de avaliação por rubrica |
| 53 | `save-command-modal` | 398 | Modal de salvar comando |
| 54 | `task-modal` | 90 | Modal de tarefa |
| 55 | `tasks-section` | 186 | Seção de tarefas |
| 56 | `template-suggestion-toast` | 252 | Toast de sugestão de template |
| 57 | `test-status-indicators` | 77 | Indicadores de status de teste |
| 58 | `timeline-section` | 144 | Seção de timeline |
| 59 | `triagem-details-modal` | 1194 | Modal de detalhes da triagem |
| 60 | `user-commands-section` | 466 | Seção de comandos do usuário |
| 61 | `war-room` | 461 | War room de recrutamento |
| 62 | `work-model-charts` | 415 | Gráficos de modelo de trabalho |

---

## Resumo por Números — Seções 1-16 (Componentes por Diretório)

| Categoria | Componentes | Linhas totais |
|-----------|------------|---------------|
| 1. UI Base (primitivos + especializados) | 64 | ~12.300 |
| 2. Chat & LIA | 22 | ~16.500 |
| 3. Job Creation & Wizard | 28 | ~14.200 |
| 4. Candidatos & Triagem | 15 | ~13.900 |
| 5. Search & Sourcing | 40 | ~18.200 |
| 6. Pipeline & Kanban (componentes) | 30 | ~10.400 |
| 7. Tables & Data | 3 | ~1.500 |
| 8. Settings & Admin | 32 | ~16.300 |
| 9. WSI | 8 | ~3.500 |
| 10. Dashboard & Analytics | 11 | ~6.500 |
| 11. Interviews & Notes | 5 | ~1.700 |
| 12. Email & Communication | 5 | ~2.500 |
| 13. Talent Funnel | 4 | ~2.500 |
| 14. Autonomous & Proactive | 5 | ~1.400 |
| 15. Layout & Navigation | 9 | ~1.400 |
| 16. Standalone (raiz) | 62 | ~38.000 |
| **Subtotal Seções 1-16** | **~343** | **~160.400** |

---

## Top 10 Maiores Componentes

> Atualizado após Sprint 4.7 (Monolith Split — -6.535L em 3 arquivos)

| # | Componente | Linhas | Observação |
|---|-----------|--------|-----------|
| 1 | `expanded-chat-modal` | 11.228 | Chat expandido — candidato a refactoring |
| 2 | `pages/candidates-page` | 8.453 | Página de candidatos — era 9.604, -1.151L Sprint 4.7 |
| 3 | `pages/job-kanban-page` | 6.308 | Página do kanban — era 8.440, -2.132L Sprint 4.7 |
| 4 | `pages/chat-page` | 5.592 | Página do chat |
| 5 | `smart-search-input` | 5.475 | Busca inteligente com NLP |
| 6 | `CompanyTeamHub` | 5.235 | Gestão de equipe |
| 7 | `pages/settings-page` | 4.449 | Configurações |
| 8 | `expandable-ai-prompt` | 4.308 | Prompt expansível |
| 9 | `pages/jobs-page` | 4.735 | Página de vagas — era 8.046, -3.309L Sprint 4.6 |
| 10 | `candidate-preview` | 2.742 | Preview de candidato — era 5.994, -3.252L Sprint 4.7 ✅ |

---

## 17. Modals (`modals/`) — 34 componentes

Diretório dedicado de modais de ação. Maior gap de documentação anterior.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `modals/add-candidate-modal` | 676 | Modal de adicionar candidato |
| 2 | `modals/add-candidates-to-vacancy-modal` | 529 | Adicionar candidatos a vaga |
| 3 | `modals/add-list-to-vacancies-modal` | 341 | Adicionar lista a vagas |
| 4 | `modals/add-to-job-modal` | 608 | Adicionar a vaga |
| 5 | `modals/add-to-list-modal` | 335 | Adicionar a lista |
| 6 | `modals/bulk-action-modal` | 440 | Modal de ação em lote |
| 7 | `modals/candidate-compare-modal` | 192 | Comparação de candidatos |
| 8 | `modals/close-vacancy-modal` | 680 | Fechar vaga |
| 9 | `modals/create-job-modal` | 406 | Criar vaga |
| 10 | `modals/create-job-with-candidates-modal` | 307 | Criar vaga com candidatos |
| 11 | `modals/data-blocking-modal` | 244 | Bloqueio de dados (LGPD) |
| 12 | `modals/data-request-modal` | 338 | Solicitação de dados |
| 13 | `modals/edit-job-modal` | 1989 | Editar vaga (componente gigante) |
| 14 | `modals/english-test-modal` | 351 | Teste de inglês |
| 15 | `modals/general-score-modal` | 267 | Score geral |
| 16 | `modals/insufficient-data-modal` | 263 | Dados insuficientes |
| 17 | `modals/job-assign-recruiter-modal` | 326 | Atribuir recrutador |
| 18 | `modals/job-compare-modal` | 1059 | Comparar vagas |
| 19 | `modals/job-duplicate-modal` | 323 | Duplicar vaga |
| 20 | `modals/job-insights-modal` | 1496 | Insights da vaga |
| 21 | `modals/job-publish-modal` | 597 | Publicar vaga |
| 22 | `modals/job-status-modal` | 1151 | Status da vaga |
| 23 | `modals/job-unpublish-modal` | 969 | Despublicar vaga |
| 24 | `modals/lia-analysis-modal` | 332 | Análise da LIA |
| 25 | `modals/new-candidate-unified-modal` | 1162 | Novo candidato unificado |
| 26 | `modals/persona-creation-modal` | 531 | Criação de persona |
| 27 | `modals/screening-media-modal` | 351 | Mídia de screening |
| 28 | `modals/share-search-modal` | 800 | Compartilhar busca |
| 29 | `modals/shared-search-details-modal` | 562 | Detalhes de busca compartilhada |
| 30 | `modals/stage-transition-actions-modal` | 946 | Ações de transição de etapa |
| 31 | `modals/technical-test-modal` | 348 | Teste técnico |
| 32 | `modals/unified-communication-modal` | 1000 | Comunicação unificada |
| 33 | `modals/unsaved-pearch-warning-modal` | 148 | Aviso de busca não salva |
| 34 | `modals/bulk-action-modal-rejection-reasons.test` | 143 | Teste unitário (TS) |

---

## 18. UI-Actions & Side Panels (`ui-actions/`) — 16 componentes

Painéis laterais e cards de ação contextual usados no fluxo de candidato/vaga.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `ui-actions/BehavioralCompetenciesPanel` | 267 | Painel de competências comportamentais |
| 2 | `ui-actions/CalibrationFeedbackPanel` | 405 | Painel de feedback de calibração |
| 3 | `ui-actions/CandidateSummaryCard` | 286 | Card resumo do candidato |
| 4 | `ui-actions/CompanyBenefitsSummaryCard` | 148 | Card resumo de benefícios |
| 5 | `ui-actions/CompensationBenefitsPanel` | 383 | Painel de compensação e benefícios |
| 6 | `ui-actions/CompensationSummaryCard` | 203 | Card resumo de compensação |
| 7 | `ui-actions/InterviewConfirmationCard` | 290 | Card de confirmação de entrevista |
| 8 | `ui-actions/InterviewSchedulingPanel` | 517 | Painel de agendamento de entrevista |
| 9 | `ui-actions/JobSummaryCard` | 321 | Card resumo da vaga |
| 10 | `ui-actions/LanguagesPanel` | 401 | Painel de idiomas |
| 11 | `ui-actions/ProgressTrackerCard` | 217 | Card de acompanhamento de progresso |
| 12 | `ui-actions/SidePanelContainer` | 183 | Container genérico de painel lateral |
| 13 | `ui-actions/TechnicalRequirementsPanel` | 385 | Painel de requisitos técnicos |
| 14 | `ui-actions/WSIQuestionsPanel` | 873 | Painel de perguntas WSI |
| 15 | `ui-actions/WSIScoreCard` | 328 | Scorecard WSI |
| 16 | `ui-actions/types` | 572 | Tipos TypeScript do módulo |

---

## 19. LIA Float (`lia-float/`) — 6 componentes

Widget flutuante da LIA — chat contextual acessível de qualquer página.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `lia-float/HITLConfirmCard` | 124 | Card de confirmação Human-in-the-Loop |
| 2 | `lia-float/LiaChatButton` | 50 | Botão flutuante de chat |
| 3 | `lia-float/LiaChatPanel` | 621 | Painel de chat flutuante |
| 4 | `lia-float/LiaFloatConditional` | 21 | Renderização condicional do float |
| 5 | `lia-float/LiaSplitPanel` | 378 | Painel split (chat + contexto) |
| 6 | `lia-float/LiaSuperPrompt` | 627 | Super prompt flutuante da LIA |

---

## 20. Notifications (`notifications/`) — 4 componentes

Sistema de notificações e toasts.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `notifications/notification-center` | 405 | Centro de notificações |
| 2 | `notifications/notification-context` | 149 | Context provider de notificações |
| 3 | `notifications/proactive-alert-toast` | 265 | Toast de alerta proativo |
| 4 | `notifications/toast-container` | 22 | Container de toasts |

---

## 21. Diretórios Menores — 31 componentes em 12 diretórios

### 21.1 Agent Control Center (`agent-control-center/`) — 3 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `agent-control-center/index` | 590 | Dashboard principal de controle de agentes |
| 2 | `agent-control-center/agent-detail-panel` | 411 | Painel de detalhe do agente |
| 3 | `agent-control-center/sparkline` | 89 | Gráfico sparkline de métricas |

### 21.2 Calibration (`calibration/`) — 2 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `calibration/calibration-dashboard` | 641 | Dashboard de calibração |
| 2 | `calibration/lia-feedback-widget` | 266 | Widget de feedback da LIA |

### 21.3 Onboarding (`onboarding/`) — 3 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `onboarding/first-access-manager` | 548 | Gerenciador de primeiro acesso |
| 2 | `onboarding/onboarding-controller` | 632 | Controlador do fluxo de onboarding |
| 3 | `onboarding/onboarding-replay-button` | 122 | Botão para replay do onboarding |

> CSS próprio: `onboarding-styles.css` (264 linhas) — classes isoladas do onboarding wizard.

### 21.4 AI Components (`ai/`) — 2 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `ai/agent-explainability-panel` | 329 | Painel de explicabilidade do agente |
| 2 | `ai/AISuggestionBadge` | 165 | Badge de sugestão da IA |

### 21.5 Alerts (`alerts/`) — 2 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `alerts/alert-settings-modal` | 609 | Modal de configuração de alertas |
| 2 | `alerts/kpi-alert-system` | 899 | Sistema de alertas KPI |

### 21.6 Benefits (`benefits/`) — 2 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `benefits/BenefitBadgeList` | 243 | Lista de badges de benefícios |
| 2 | `benefits/BenefitDetailsSheet` | 303 | Sheet de detalhes do benefício |

### 21.7 Screening & Config (`screening/`, `screening-config/`) — 9 componentes

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `screening/screening-notification-card` | 158 | Card de notificação de triagem |
| 2 | `screening-config/CompanyBankQuestions` | 314 | Banco de perguntas da empresa |
| 3 | `screening-config/CustomQuestions` | 275 | Perguntas customizadas |
| 4 | `screening-config/ScreeningChannelsModal` | 164 | Modal de canais de triagem |
| 5 | `screening-config/ScreeningConfigManager` | 2402 | Gerenciador de config (componente gigante) |
| 6 | `screening-config/ScreeningSchedulingModal` | 217 | Modal de agendamento |
| 7 | `screening-config/ScreeningScriptTab` | 618 | Tab de script de triagem |
| 8 | `screening-config/ScreeningSettingsModal` | 188 | Modal de configurações |
| 9 | `screening-config/ScreeningStatusModal` | 401 | Modal de status |

### 21.8 Componentes Unitários (1 componente cada)

| # | Componente | Linhas | Dir | Função |
|---|-----------|--------|-----|--------|
| 1 | `filters/robust-filters` | 429 | `filters/` | Filtros avançados robustos |
| 2 | `lists/add-candidate-to-list-modal` | 522 | `lists/` | Modal de adicionar candidato a lista |
| 3 | `ml/recruitment-ml-engine` | 643 | `ml/` | Engine de ML de recrutamento |
| 4 | `module-access/module-upsell` | 299 | `module-access/` | Upsell de módulo premium |
| 5 | `reports/advanced-report-exporter` | 517 | `reports/` | Exportador de relatórios avançado |
| 6 | `report-scheduler/report-scheduler` | 644 | `report-scheduler/` | Agendador de relatórios |
| 7 | `score/ScoreBreakdownBadge` | 293 | `score/` | Badge de breakdown de score |
| 8 | `async/AsyncJobProgress` | 247 | `async/` | Progresso de jobs assíncronos |

---

## 22. Pages Sub-Components (`pages/`) — 15 sub-componentes + 3 hooks + 3 types + 27 páginas standalone

Componentes extraídos dentro de subdiretórios de páginas.

### 22.1 Candidates Module (`pages/candidates/`)

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `CandidateSearchBar` | 146 | Barra de busca de candidatos |
| 2 | `CandidatesFilterPanel` | 1124 | Painel de filtros (componente gigante) |
| 3 | `CandidatesHeader` | 66 | Header da lista |
| 4 | `CandidatesTable` | 386 | Tabela de candidatos |
| 5 | `CandidateTabs` | 53 | Tabs do candidato |
| 6 | `SearchResultsHeader` | 233 | Header de resultados |
| 7 | `hooks/useCandidatesQuery` | 232 | Hook de query de candidatos |
| 8 | `hooks/useCandidatesSelection` | 121 | Hook de seleção |
| 9 | `types` | 230 | Tipos do módulo |
| 10 | `CreditConfirmationModal` | 156 | Modal de confirmação de créditos (busca global Pearch) — **Sprint 4.6** |
| 11 | `SaveAsArchetypeModal` | 181 | Modal para salvar query como arquétipo — **Sprint 4.6** |
| 12 | `EditQueryModal` | 131 | Modal para editar query de busca com SmartSearchInput — **Sprint 4.6** |
| 13 | `PreviewSuggestionModal` | 317 | Modal de preview/edição de sugestão IA de arquétipo — **Sprint 4.6** |

### 22.2 Job Kanban Module (`pages/job-kanban/`)

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `KanbanCard` | 180 | Card do kanban de página |
| 2 | `KanbanColumn` | 95 | Coluna do kanban de página |
| 3 | `MoveConfirmationModal` | 198 | Modal de confirmação de movimento |
| 4 | `hooks/useKanbanState` | 207 | Hook de estado do kanban |
| 5 | `types` | 90 | Tipos do módulo |
| 6 | `KanbanFiltersPanel` | 184 | Painel de filtros do kanban (score, status, origem, modelo) — **Sprint 4.6** |
| 7 | `KanbanColumnConfigPanel` | 194 | Configuração de colunas visíveis do kanban — **Sprint 4.6** |
| 8 | `AddColumnPopover` | 266 | Popover para adicionar nova etapa ao pipeline — **Sprint 4.6** |

### 22.3 Jobs Module (`pages/jobs/`)

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `JobsHeader` | 119 | Header de vagas |
| 2 | `JobsTable` | 269 | Tabela de vagas |
| 3 | `hooks/useJobsQuery` | 206 | Hook de query de vagas |
| 4 | `types` | 106 | Tipos do módulo |
| 5 | `ColumnConfigPanel` | 174 | Configuração de colunas visíveis da tabela de vagas — **Sprint 4.6** |
| 6 | `TableFiltersPanel` | 516 | Painel de filtros avançados da tabela de vagas — **Sprint 4.6** |
| 7 | `InlineChatPanel` | 718 | Sidebar LIA inline (chat + criação de vaga + templates) — **Sprint 4.6** |
| 8 | `JobPreviewPanel` | 1926 | Painel lateral de preview de vaga (detalhes + pipeline analytics) — **Sprint 4.6** |

### 22.4 Candidate Preview Sub-Components (`candidate-preview/`)

Subdiretório novo criado no Sprint 4.6 para componentes extraídos de `candidate-preview.tsx`.

| # | Componente | Linhas | Função |
|---|-----------|--------|--------|
| 1 | `FilePreviewModal` | 548 | Modal de preview de arquivos (PDF, imagem, vídeo, áudio) — **Sprint 4.6** |
| 2 | `LiaChatModal` | 316 | Modal de chat LIA no contexto do candidato — **Sprint 4.6** |

### 22.5 Páginas Standalone (`pages/`)

| # | Página | Linhas | Função |
|---|--------|--------|--------|
| 1 | `ai-credits-page` | 276 | Créditos IA |
| 2 | `ats-integrations-page` | 1522 | Integrações ATS |
| 3 | `big-five-dashboard-page` | 640 | Dashboard Big Five |
| 4 | `candidate-review-modal` | 822 | Modal de revisão de candidato |
| 5 | `candidates-page` | 9604 | Página de candidatos (3º maior) — era 10.329, -721L no Sprint 4.6 |
| 6 | `chat-page` | 5592 | Página de chat |
| 7 | `dashboards-page` | 3283 | Página de dashboards |
| 8 | `executive-dashboard-page` | 680 | Dashboard executivo |
| 9 | `indicators-page` | 1753 | Página de indicadores |
| 10 | `integrations-page` | 804 | Página de integrações |
| 11 | `job-kanban-page` | 8440 | Página do kanban (2º maior) — era 10.377, -1.934L no Sprint 4.6 |
| 12 | `jobs-page` | 4735 | Página de vagas — era 8.046, -3.309L no Sprint 4.6 |
| 13 | `jobs2-page` | 569 | Página de vagas v2 |
| 14 | `job-templates-page` | 549 | Templates de vagas |
| 15 | `lia-library-page` | 408 | Biblioteca LIA |
| 16 | `login-page` | 627 | Página de login |
| 17 | `mockup-shadcn-vue-page` | 599 | Mockup shadcn/vue |
| 18 | `onboarding-page` | 830 | Onboarding |
| 19 | `onboarding-premium-page` | 915 | Onboarding premium |
| 20 | `real-time-dashboard-page` | 498 | Dashboard real-time |
| 21 | `settings-page` | 4449 | Configurações |
| 22 | `settings-page-enhanced` | 623 | Configurações melhoradas |
| 23 | `tasks-page` | 2192 | Tarefas |
| 24 | `tasks-page-mvp` | 890 | Tarefas MVP |
| 25 | `templates-page` | 492 | Templates |
| 26 | `workflow-automation-page` | 640 | Automação de workflow |
| 27 | `work-model-analytics-page` | 567 | Analytics de modelo de trabalho |

### 22.6 Pendências de Split — Monolitos Restantes

Arquivos ainda acima de 5.000 linhas após Sprint 4.7:

| Arquivo | Linhas atuais | Blocos identificados para extração |
|---------|--------------|-----------------------------------|
| `candidates-page.tsx` | 8.453 | Bloco search results (`activeTab === 'search' && showSearchResults`, ~864L) contendo compact LIA bar + layout de resultados |
| `job-kanban-page.tsx` | 6.308 | Superchat view (~80L), tab de edição de vaga (~400L) |
| `expanded-chat-modal.tsx` | 11.228 | Candidato a Sprint 4.9 — maior monolito restante |
| `smart-search-input.tsx` | 5.475 | Candidato a Sprint 4.9 |
| `CompanyTeamHub.tsx` | 5.235 | Candidato a Sprint 4.9 |

> **Critério de priorização:** extrair blocos >400L que sejam autocontidos (estado próprio + props claras).
> **Próxima sprint de split sugerida:** Sprint 4.8 — candidates-page search results view (~864L) + expanded-chat-modal.

---

## 23. Custom Hooks (`src/hooks/`) — 93 hooks

Hooks customizados que encapsulam lógica de negócio, state management e integrações com API.

| # | Hook | Linhas | Domínio |
|---|------|--------|---------|
| 1 | `use-action-intent` | 172 | Intenção de ação do usuário |
| 2 | `useAgentMemory` | 95 | Memória do agente IA |
| 3 | `use-agent-streaming` | 310 | Streaming de respostas do agente |
| 4 | `use-ai-consumption` | 115 | Monitoramento de consumo IA |
| 5 | `use-ai-credits` | 130 | Créditos de IA |
| 6 | `use-archetypes` | 427 | Gestão de arquétipos |
| 7 | `use-bias-audit-report` | 95 | Relatório de auditoria de viés |
| 8 | `use-bulk-selection` | 197 | Seleção em massa |
| 9 | `use-candidate-compare` | 86 | Comparação de candidatos |
| 10 | `use-candidate-data-requests` | 278 | Solicitações de dados de candidato |
| 11 | `use-candidate-filters` | 227 | Filtros de candidato |
| 12 | `use-candidate-selection` | 107 | Seleção de candidato |
| 13 | `use-candidates-list-mapped` | 55 | Lista mapeada de candidatos |
| 14 | `use-candidates-list` | 149 | Lista de candidatos |
| 15 | `useCandidateSuggestions` | 107 | Sugestões de candidato |
| 16 | `useChatLayout` | 77 | Layout do chat |
| 17 | `use-clients` | 185 | Gestão de clientes |
| 18 | `use-communication-templates` | 586 | Templates de comunicação |
| 19 | `use-company-benefits` | 126 | Benefícios da empresa |
| 20 | `useCompanyBenefits` | 141 | Benefícios da empresa (v2) |
| 21 | `use-company-culture` | 210 | Cultura da empresa |
| 22 | `use-company-defaults` | 103 | Defaults da empresa |
| 23 | `use-company-eligibility-questions` | 93 | Perguntas de elegibilidade |
| 24 | `use-company-lia-instructions` | 420 | Instruções LIA da empresa |
| 25 | `use-company-managers` | 165 | Gestores da empresa |
| 26 | `use-company-pipeline` | 73 | Pipeline da empresa |
| 27 | `useCompanySkillsCatalog` | 185 | Catálogo de skills |
| 28 | `use-company-tech-stack` | 131 | Tech stack da empresa |
| 29 | `useCreditEstimator` | 188 | Estimador de créditos |
| 30 | `use-current-company` | 54 | Empresa atual |
| 31 | `use-current-scope` | 83 | Escopo atual (global/cliente) |
| 32 | `use-daily-briefing` | 114 | Briefing diário |
| 33 | `use-data-request-config` | 430 | Config de solicitação de dados |
| 34 | `use-data-request-modals` | 83 | Modais de solicitação |
| 35 | `useDynamicSuggestions` | 212 | Sugestões dinâmicas |
| 36 | `use-edit-lock` | 116 | Lock de edição |
| 37 | `use-empty-field-notifications` | 179 | Notificações de campos vazios |
| 38 | `useFastTrack` | 470 | Fast track de candidato |
| 39 | `use-float-conversation` | 150 | Conversa flutuante |
| 40 | `use-float-streaming` | 200 | Streaming flutuante |
| 41 | `useGlobalSearchSettings` | 88 | Configurações de busca global |
| 42 | `useHideViewedCandidates` | 168 | Esconder candidatos visualizados |
| 43 | `use-hiring-policies` | 261 | Políticas de contratação |
| 44 | `use-interpret-context` | 184 | Interpretação de contexto |
| 45 | `use-job-analytics` | 119 | Analytics de vaga |
| 46 | `useJobColumnConfig` | 261 | Config de colunas de vaga |
| 47 | `use-job-draft` | 231 | Rascunho de vaga |
| 48 | `useJobFiltersPersistence` | 224 | Persistência de filtros de vaga |
| 49 | `use-job-report` | 63 | Relatório de vaga |
| 50 | `use-job-wizard-backend` | 495 | Backend do wizard de vaga |
| 51 | `use-keyboard-shortcuts` | 182 | Atalhos de teclado |
| 52 | `use-lia-suggestions` | 314 | Sugestões da LIA |
| 53 | `use-ml-predictions` | 144 | Predições ML |
| 54 | `use-navigation-intent` | 52 | Intenção de navegação |
| 55 | `use-navigation-persistence` | 102 | Persistência de navegação |
| 56 | `use-override-approve` | 78 | Override de aprovação |
| 57 | `use-page-theme` | 55 | Tema por página |
| 58 | `use-pipeline-inheritance` | 73 | Herança de pipeline |
| 59 | `use-proactive-alerts` | 137 | Alertas proativos |
| 60 | `use-proactive-insights` | 88 | Insights proativos |
| 61 | `use-recent-items` | 86 | Itens recentes |
| 62 | `use-recruitment-stages` | 126 | Estágios de recrutamento |
| 63 | `use-return-events` | 233 | Eventos de retorno |
| 64 | `use-saas-metrics` | 152 | Métricas SaaS |
| 65 | `use-scim-config` | 93 | Config SCIM |
| 66 | `use-score-breakdown` | 79 | Breakdown de score |
| 67 | `useScreeningConfig` | 246 | Config de screening |
| 68 | `use-screening-questions` | 438 | Perguntas de screening |
| 69 | `use-search-autocomplete` | 111 | Autocomplete de busca |
| 70 | `use-search-entities` | 436 | Entidades de busca |
| 71 | `useSearchFlow` | 136 | Fluxo de busca |
| 72 | `use-search-source` | 102 | Fonte de busca |
| 73 | `useSemanticSearch` | 199 | Busca semântica |
| 74 | `useSessionRefresh` | 66 | Refresh de sessão |
| 75 | `use-short-list` | 165 | Short list |
| 76 | `use-similar-profiles` | 176 | Perfis similares |
| 77 | `use-sub-status-panel` | 76 | Painel de sub-status |
| 78 | `useTableFeatures` | 373 | Features de tabela |
| 79 | `use-table-features` | 228 | Features de tabela (v2) |
| 80 | `use-talent-funnel` | 475 | Funil de talentos |
| 81 | `use-template-suggestions` | 259 | Sugestões de template |
| 82 | `use-toast` | 191 | Toasts |
| 83 | `use-transition-context` | 694 | Contexto de transição (maior hook) |
| 84 | `use-triagem-chat` | 536 | Chat de triagem |
| 85 | `useUIActions` | 255 | Ações de UI |
| 86 | `useUnifiedSearch` | 139 | Busca unificada |
| 87 | `use-wizard-auto-save` | 418 | Auto-save do wizard |
| 88 | `use-wizard-suggestions` | 226 | Sugestões do wizard |
| 89 | `use-workforce-planning` | 212 | Planejamento de workforce |
| 90 | `use-workos-metrics` | 31 | Métricas WorkOS |
| 91 | `use-wsi-async` | 104 | WSI assíncrono |

**Hooks em subdiretórios de componentes (27 adicionais):**

| # | Hook | Dir | Linhas | Função |
|---|------|-----|--------|--------|
| 1 | `useChatSync` | `expanded-chat/hooks/` | 362 | Sincronização do chat |
| 2 | `useContextSwitching` | `expanded-chat/hooks/` | 342 | Troca de contexto |
| 3 | `useConversationMemory` | `expanded-chat/hooks/` | 425 | Memória de conversa |
| 4 | `useFieldHighlight` | `expanded-chat/hooks/` | 87 | Highlight de campo |
| 5 | `useLearning` | `expanded-chat/hooks/` | 401 | Aprendizado do chat |
| 6 | `useToolCalling` | `expanded-chat/hooks/` | 323 | Chamada de tools |
| 7 | `useWizardAnalytics` | `expanded-chat/hooks/` | 369 | Analytics do wizard |
| 8 | `useWizardNavigation` | `expanded-chat/hooks/` | 257 | Navegação do wizard |
| 9 | `useWizardOrchestrator` | `expanded-chat/hooks/` | 268 | Orquestrador do wizard |
| 10 | `useWizardState` | `expanded-chat/hooks/` | 439 | Estado do wizard |
| 11 | `useWSIQualityGates` | `expanded-chat/hooks/` | 169 | Quality gates WSI |
| 12 | `useStageValidation` | `job-wizard/hooks/` | 183 | Validação de estágio |
| 13 | `useWizardNavigation` | `job-wizard/hooks/` | 66 | Navegação do wizard |
| 14-19 | *(kanban hooks)* | `kanban/hooks/` | 736 | *(documentados na seção 6)* |
| 20 | `useCandidatesQuery` | `pages/candidates/hooks/` | 232 | Query de candidatos |
| 21 | `useCandidatesSelection` | `pages/candidates/hooks/` | 121 | Seleção |
| 22 | `useKanbanState` | `pages/job-kanban/hooks/` | 207 | Estado do kanban |
| 23 | `useJobsQuery` | `pages/jobs/hooks/` | 206 | Query de vagas |
| 24 | `use-table-columns` | `tables/hooks/` | 129 | Colunas de tabela |
| 25 | `use-table-selection` | `tables/hooks/` | 63 | Seleção em tabela |
| 26 | `use-table-sorting` | `tables/hooks/` | 75 | Ordenação em tabela |

> **Total de hooks:** 93 (raiz) + 27 (componentes) = **120 custom hooks**

---

## 24. Contexts & Providers — 5 contextos

> **Nota:** `auth-context` e `theme-provider` também aparecem na seção 15 (Layout & Navigation) como componentes de UI. Aqui estão documentados como providers de estado global — são os mesmos arquivos, com duplo papel.

| # | Context | Localização | Linhas | Função |
|---|---------|-------------|--------|--------|
| 1 | `auth-context` | `src/contexts/auth-context.tsx` | ~100 | Autenticação WorkOS + sessão |
| 2 | `lia-float-context` | `src/contexts/lia-float-context.tsx` | ~150 | Estado do widget flutuante LIA |
| 3 | `notification-context` | `components/notifications/notification-context.tsx` | 149 | Notificações globais |
| 4 | `theme-provider` | `components/theme-provider.tsx` | 16 | Provider de tema (next-themes) |
| 5 | `ExpandedChatContext` | `components/expanded-chat/ExpandedChatContext.tsx` | 250 | Estado do chat expandido |

> **Nota:** `auth-context.tsx` na raiz de components é um wrapper de 21 linhas que re-exporta do `src/contexts/auth-context.tsx`.

---

## 25. Types, Constants & Config — 3 arquivos de types + 13 arquivos lib

### 25.1 Types (`src/types/`)

| # | Arquivo | Linhas | Conteúdo |
|---|---------|--------|----------|
| 1 | `benefits.ts` | 74 | Tipos de benefícios |
| 2 | `interview-notes.ts` | 225 | Tipos de notas de entrevista |
| 3 | `wizard-suggestions.ts` | 113 | Tipos de sugestões do wizard |

### 25.2 Lib Utilities (`src/lib/`)

| # | Arquivo | Linhas | Conteúdo |
|---|---------|--------|----------|
| 1 | `design-tokens.ts` | 644 | Tokens TypeScript — colors, typography, spacing, shadows, textStyles, cardStyles, buttonStyles, badgeStyles, tabStyles, tailwindToVuetify mapping (512 linhas ativas) |
| 2 | `recruitment-stages.ts` | 974 | Estágios de recrutamento — definição, cores, transições |
| 3 | `industry-constants.ts` | 747 | Constantes de indústrias (747 linhas) |
| 4 | `template-variables.ts` | 393 | Variáveis para templates de email |
| 5 | `hiring-policy-utils.ts` | 193 | Utilitários de políticas de contratação |
| 6 | `chat-format.ts` | 122 | Formatação de mensagens de chat |
| 7 | `theme-colors.ts` | 114 | **6 temas por página (54 cores hardcoded fora do DS)** |
| 8 | `session-crypto.ts` | 71 | Criptografia de sessão |
| 9 | `workos.ts` | 39 | Config WorkOS |
| 10 | `workos-session.ts` | 10 | Sessão WorkOS |
| 11 | `workos-links.ts` | 32 | Links WorkOS |
| 12 | `chat-commands.ts` | 14 | Comandos de chat |
| 13 | `utils.ts` | 6 | Utilitário cn() (classnames) |

> **Alerta:** `theme-colors.ts` define 6 temas de página com 54 cores hardcoded que **não usam tokens do design system**. Ver seção 28.6.

---

## 26. App Routes — 90 page routes + 5 layouts

### 26.1 Layouts (5)

| # | Layout | Caminho |
|---|--------|---------|
| 1 | Root Layout | `layout.tsx` |
| 2 | Admin Layout | `admin/layout.tsx` |
| 3 | Admin Client Layout | `admin/clientes/[clientId]/layout.tsx` |
| 4 | Admin Compliance Layout | `admin/compliance/layout.tsx` |
| 5 | Triagem Layout | `triagem/[token]/layout.tsx` |

### 26.2 Rotas Públicas (12)

| # | Rota | Função |
|---|------|--------|
| 1 | `/login` | Login |
| 2 | `/login/welcome` | Boas-vindas |
| 3 | `/register` | Registro |
| 4 | `/forgot-password` | Esqueceu senha |
| 5 | `/reset-password` | Reset de senha |
| 6 | `/accept-invitation` | Aceitar convite |
| 7 | `/aceitar-convite` | Aceitar convite (PT) |
| 8 | `/access` | Acesso |
| 9 | `/triagem/[token]` | Triagem pública |
| 10 | `/shared/[token]` | Compartilhamento |
| 11 | `/portal/data-request/[token]` | Portal de dados |
| 12 | `/vagas/[slug]` | Vaga pública |

### 26.3 Rotas Autenticadas — App Principal (13)

| # | Rota | Função |
|---|------|--------|
| 1 | `/` (home) | Dashboard principal |
| 2 | `/chat` | Chat com LIA |
| 3 | `/jobs` | Lista de vagas |
| 4 | `/jobs/[id]` | Detalhe da vaga + kanban |
| 5 | `/funil` | Funil de talentos |
| 6 | `/funil-de-talentos` | Funil de talentos (v2) |
| 7 | `/funil-de-talentos/candidato/[id]` | Candidato no funil |
| 8 | `/tasks` | Tarefas |
| 9 | `/tasks-mvp` | Tarefas MVP |
| 10 | `/configuracoes` | Configurações |
| 11 | `/configuracoes/ai-credits` | Créditos IA |
| 12 | `/configuracoes/integracoes` | Integrações |
| 13 | `/ajuda` | Ajuda |

### 26.4 Rotas Admin (56)

Administração de clientes, compliance, monitoramento e configurações globais.

| Grupo | Rotas | Exemplos |
|-------|-------|---------|
| Clientes | 22 | `/admin/clientes/[clientId]/setup`, `big-five`, `comunicacoes`, `consumo-ia`, `faturamento`, `integracoes`, `metricas`, `observabilidade`, `testes`, `usuarios`, `workforce`, `conformidade/*` |
| Compliance | 25 | `/admin/compliance/auditoria/*`, `controles/*`, `guardrails`, `health-check`, `lgpd/*`, `monitoramento/*`, `riscos/*`, `trust-center/*` |
| Config & Outros | 9 | `/admin/configuracoes/*`, `jornada-recrutamento`, `metricas-plataforma`, `monitoring/agents`, `onboarding-clientes`, `setup-empresa`, `sso`, `templates` |

### 26.5 Rotas Utilitárias (9)

| # | Rota | Função |
|---|------|--------|
| 1 | `/privacidade` | Política de privacidade |
| 2 | `/trust` | Trust center |
| 3 | `/upgrade` | Upgrade de plano |
| 4-9 | Auth callbacks | WorkOS SSO, refresh, etc. |

---

## 27. API Routes — 424 endpoints

Todas as rotas de API do Next.js em `src/app/api/`.

| Categoria | Endpoints | Descrição |
|-----------|-----------|-----------|
| `backend-proxy/*` | 402 | Proxy para o backend Python (lia-agent-system) |
| `ai/*` | 9 | Sugestões IA (empresas, skills, universidades, indústrias) |
| `auth/workos/*` | 4 | Autenticação WorkOS (callback, refresh, session, SSO) |
| `public-proxy/*` | 4 | Proxy público (shared links, OTP) |
| `admin/*` | 1 | Dashboard summary admin |
| `jira` | 1 | Integração Jira |
| `lia/*` | 1 | Proxy LIA catch-all |
| `portal/*` | 1 | Portal de data request |
| `webhooks/workos` | 1 | Webhook WorkOS |

> **Nota:** 95% dos endpoints são `backend-proxy/*` — o frontend Next.js funciona como BFF (Backend for Frontend) fazendo proxy para o `lia-agent-system` Python.

**Principais domínios de API:**

| Domínio | Endpoints | Operações |
|---------|-----------|-----------|
| Candidatos | ~25 | CRUD, bulk ops, favorites, hide, search |
| Vagas (Jobs) | ~20 | CRUD, publish, duplicate, analytics |
| WSI (Screening) | ~15 | Generate questions, evaluate, F11 report |
| Billing | ~10 | Subscription, invoices, payment methods |
| Agent Monitoring | ~12 | Agents, activities, metrics, health |
| Aprovações | ~6 | CRUD, approve, reject, cancel |
| Compliance/Audit | ~10 | Logs, retention, export |
| Calendar | ~4 | Interviews, Google auth, reschedule |
| Workforce | ~8 | Planning, stats, headcounts |
| Automações | ~5 | CRUD, triggers |

---

## 28. CSS Infrastructure & Style System

### 28.1 CSS Variables — 242 variáveis em 2 arquivos

**`design-tokens.css` (:root) — 92 variáveis (fonte de verdade):**

| Categoria | Variáveis | Exemplos |
|-----------|-----------|---------|
| Backgrounds | 4 | `--lia-bg-primary`, `--lia-bg-secondary`, `--lia-bg-tertiary`, `--lia-bg-hover` |
| Borders | 3 | `--lia-border-subtle`, `--lia-border-default`, `--lia-border-strong` |
| Text | 5 | `--lia-text-primary` (#111827), `--lia-text-secondary`, `--lia-text-tertiary`, `--lia-text-disabled`, `--lia-text-inverse` |
| Interactive | 3 | `--lia-interactive-primary`, `--lia-interactive-hover`, `--lia-interactive-active` |
| Shadows | 4 | `--lia-shadow-sm`, `--lia-shadow-default`, `--lia-shadow-md`, `--lia-shadow-lg` |
| Brand WeDo | 4 | `--lia-brand-primary`, `--lia-brand-secondary`, `--lia-brand-accent`, `--lia-brand-light` |
| WeDo Colors | 18 | `--wedo-cyan` (#60BED1), `--wedo-green`, `--wedo-orange`, `--wedo-purple`, `--wedo-magenta`, etc. |
| Status | 12 | `--lia-status-success`, `--lia-status-error`, `--lia-status-warning`, `--lia-status-info`, `--lia-cat-*` |
| Components | 15 | `--lia-card-bg`, `--lia-input-bg`, `--lia-sidebar-bg`, etc. |
| Typography | 7 | `--font-size-xs` (11px), `--font-size-micro` (10px), `--font-size-sm-ui` (12px), `--font-size-base-ui` (13px), etc. |
| Gray Scale | 8 | `--lia-gray-50` a `--lia-gray-900` |
| Chart | 4 | `--lia-chart-1` a `--lia-chart-4` |
| Text Hierarchy | 8 | `--heading-*`, `--body-*` |

**`globals.css` (@layer base :root) — 150 variáveis adicionais:**

| Categoria | Variáveis | Notas |
|-----------|-----------|-------|
| Font vars | 4 | `--font-open-sans`, `--font-inter`, `--font-jetbrains`, `--font-source-serif` |
| ElevenLabs theme | 15+ | `--eleven-text-*`, `--eleven-surface-*` — sistema paralelo |
| shadcn/ui vars | 23 | `--background`, `--foreground`, `--card`, `--primary`, etc. |
| Misc | ~108 | Cores de componentes específicos |

**Dark Mode:** Todas as 92 variáveis de `design-tokens.css` têm overrides em `.dark {}`. Coverage: **100%**.

> **Problema identificado:** Duplicação entre `--lia-text-primary: #111827` (design-tokens.css) e `--eleven-text-primary: #2D2D2D` (globals.css) — dois sistemas concorrentes.

### 28.2 Animações & Keyframes — 29 definições

| Grupo | Keyframes | Status |
|-------|-----------|--------|
| Core (usados) | `fade-in`, `slideDown`, `slideUp`, `shimmer` | Ativos |
| UI transitions | `fadeIn`, `slideIn`, `scaleIn`, `slideInRight`, `slideInUp`, `slideOutUp`, `slideOutLeft`, `fadeOut`, `fadeInUp`, `fadeInDown` | Ativos |
| Especializado | `dotsPulse`, `slideInFromRight`, `scaleRotateIn`, `scaleInDelayed`, `progressShrink`, `realtimePulse`, `pulse-subtle`, `spin-smooth`, `loading-skeleton` | Ativos |
| LIA | `searchPulse`, `sonarRing`, `sonarRing2`, `lia-glow-pulse`, `lia-sound-wave`, `lia-speaking-glow-pulse` | Ativos |

> **Nota:** Muitas animações Radix são neutralizadas com `animation: none !important` no CSS. O sistema visual é majoritariamente estático.

### 28.3 Z-Index — 15 valores sem escala semântica

| Valor | Onde usado | Propósito |
|-------|-----------|----------|
| `z-0` a `z-30` | Componentes base | Camadas normais |
| `z-40`, `z-50` | Dropdowns, popovers | Overlays leves |
| `z-[60]` | Modais secundários | Modais sobre modais |
| `z-[100]` | Toasts, alertas | Notificações |
| `z-[200]` | SelectContent em modais | Dropdowns sobre modais |
| `z-[9998]` | Dialog overlay | Backdrop de dialog |
| `z-[9999]` | Dialog content, modais críticos | Conteúdo de dialog |
| `z-[10000]` | Variable selector | Máximo absoluto |

> **Problema:** Escala inflada (0 a 10000) sem naming semântico. Referências de mercado (Linear, Vercel) usam: `z-base`, `z-dropdown`, `z-modal`, `z-toast`, `z-max`.

### 28.4 Classes CSS Customizadas — 200+ classes

**`design-tokens.css` — 58 classes:**

| Grupo | Classes | Exemplos |
|-------|---------|---------|
| Backgrounds | 3 | `.lia-bg-primary`, `.lia-bg-secondary`, `.lia-bg-tertiary` |
| Text | 3 | `.lia-text-primary`, `.lia-text-secondary`, `.lia-text-tertiary` |
| WeDo Text | 4 | `.wedo-text-title`, `.wedo-text-body`, `.wedo-text-secondary`, `.wedo-text-muted` |
| Borders | 2 | `.lia-border-subtle`, `.lia-border-default` |
| Brand | 3 | `.lia-brand-text`, `.lia-brand-bg`, `.lia-brand-border` |
| Shadows | 4 | `.lia-shadow-sm`, `.lia-shadow`, `.lia-shadow-md`, `.lia-shadow-lg` |
| Typography | 12 | `.lia-h1` a `.lia-h4`, `.lia-subtitle`, `.lia-body`, `.lia-caption`, `.lia-label`, etc. |
| Cards | 3 | `.lia-card`, `.lia-card-elevated`, `.lia-card-hover` |
| Buttons | 3 | `.lia-btn-primary`, `.lia-btn-secondary`, `.lia-btn-ghost` |
| Badges | 6+ | `.lia-badge`, `.lia-badge-jobs`, `.lia-badge-candidates`, etc. |

**`globals.css` — 142+ classes** (animações, sidebar, scrollbar, ElevenLabs, etc.)

### 28.5 Breakpoints — Uso quantificado

| Breakpoint | Tamanho | Usos | % |
|-----------|---------|------|---|
| `sm:` | 640px | 270 | 31% |
| `md:` | 768px | 328 | 37% (mais usado) |
| `lg:` | 1024px | 252 | 29% |
| `xl:` | 1280px | 23 | 3% |
| `2xl:` | 1536px | 9 | <1% |

> **Insight:** App é desktop-first — 97% dos breakpoints são sm/md/lg. xl/2xl quase não usados.

### 28.6 Sistema de Temas por Página — 6 temas (fora do DS)

`src/lib/theme-colors.ts` define 6 temas com **54 cores hardcoded** que não usam tokens:

| Página | Primary | Accent | Status |
|--------|---------|--------|--------|
| Chat com LIA | `#0094c6` | `#00b8d4` | Fora do DS — deveria ser `--wedo-cyan` |
| Tarefas | `#f0b323` | `#f9a825` | Fora do DS — cor inexistente no DS |
| Candidatos | `#8bb923` | `#7cb342` | Fora do DS — deveria ser `--wedo-green` |
| Vagas | `#de1c31` | `#e53935` | Fora do DS — cor inexistente no DS |
| Indicadores | `#f6a68c` | `#ff8a65` | Fora do DS — cor inexistente no DS |
| Biblioteca LIA | `#8b5cf6` | `#7c3aed` | Fora do DS — deveria ser `--wedo-purple` |

### 28.7 Sistema de Ícones — 169 ícones Lucide

| Métrica | Valor |
|---------|-------|
| Biblioteca | `lucide-react` |
| Ícones únicos importados | 169 |
| Arquivos que usam ícones | 485 |
| Ícone LIA dedicado | Sim (`lia-icon.tsx` — componente customizado) |

> Não existe catálogo visual ou mapa de quais ícones representam quais conceitos.

### 28.8 Tipografia — Uso quantificado completo

**Tamanhos:**

| Tamanho | Token | Pixels | Usos |
|---------|-------|--------|------|
| `text-xs` | `--font-size-xs` | 11px | 7.066 (dominante) |
| `text-sm` | Tailwind default | 14px | 3.339 |
| `text-micro` | `--font-size-micro` | 10px | 2.058 |
| `text-base` | Tailwind default | 16px | 440 |
| `text-lg` | Tailwind default | 18px | 465 |
| `text-2xl` | Tailwind default | 24px | 380 |
| `text-xl` | Tailwind default | 20px | 187 |
| `text-base-ui` | `--font-size-base-ui` | 13px | 178 |
| `text-3xl` | Tailwind default | 30px | 48 |
| `text-sm-ui` | `--font-size-sm-ui` | 12px | 18 |
| `text-4xl` | Tailwind default | 36px | 10 |

> **Fase 1 concluída:** Zero valores arbitrários `text-[*px]` restam no código.

**Fontes:**

| Família | Arquivos | Papel | % |
|---------|----------|-------|---|
| Open Sans | 177 | Principal | 85% |
| JetBrains Mono | 51 | Monospace/código | 5% |
| Inter | 15 | Dados/números | 10% |
| Source Serif | 4 | Legacy (removendo) | <1% |
| Crimson | 3 | Legacy (removendo) | <1% |

**Pesos:**

| Peso | Classe | Usos |
|------|--------|------|
| 500 | `font-medium` | 3.939 (dominante) |
| 600 | `font-semibold` | 1.785 |
| 700 | `font-bold` | 758 |
| 400 | `font-normal` | 66 |
| 300 | `font-light` | 5 |

### 28.9 Dark Mode — Cobertura

| Métrica | Valor |
|---------|-------|
| Total de classes `dark:` | 16.058 usos |
| Classes únicas com `dark:` | 205 |
| Design tokens com override `.dark` | 92 (100% cobertura) |

### 28.10 Gradientes — 52 ocorrências

Direção principal: `bg-gradient-to-b` (vertical) com `from-gray-*` / `to-gray-*`. Poucas exceções com `linear-gradient()` inline.

### 28.11 CSS Modulares — 4 arquivos, 2.663 linhas

| Arquivo | Linhas | Escopo |
|---------|--------|--------|
| `src/styles/design-tokens.css` | 820 | Global — tokens, classes, dark mode |
| `src/app/globals.css` | 1477 | Global — base, animações, components |
| `src/styles/onboarding-styles.css` | 264 | Isolado — onboarding wizard |
| `src/styles/chat-page.css` | 102 | Isolado — página de chat |

### 28.12 Testes de Componentes

| Arquivo | Linhas | O que testa |
|---------|--------|-------------|
| `__tests__/fairness-warning-banner.test.tsx` | 40 | Banner de fairness |
| `__tests__/lia-score-card.test.tsx` | 53 | Scorecard LIA |
| `__tests__/ml-insights-card.test.tsx` | 139 | Card de insights ML |
| `lia-float/LiaChatPanel-p2c.test.tsx` | 227 | Painel de chat flutuante |
| `kanban/utils/__tests__/stage-utils.test.ts` | 223 | Utilitários de estágios |

> **Cobertura de testes:** 5 arquivos de teste para 556 componentes — **<1% de cobertura**.

---

## Resumo Expandido — Inventário 100%

| Dimensão | Quantidade | Status |
|----------|-----------|--------|
| Componentes documentados (seções 1-22) | 556 | 100% coberto |
| Custom hooks | 120 | 100% coberto |
| Contexts & providers | 5 | 100% coberto |
| Types & config files | 17 | 100% coberto |
| Lib utilities | 13 | 100% coberto |
| Page routes | 90 | 100% coberto |
| API endpoints | 424 | 100% coberto |
| CSS variables | 242 | 100% coberto |
| Keyframe animations | 29 | 100% coberto |
| Custom CSS classes | 200+ | 100% coberto |
| Ícones catalogados | 169 | 100% coberto |
| Breakpoints quantificados | 5 | 100% coberto |
| Dark mode coverage | 16.058 usos | 100% coberto |
| Tipografia quantificada | 11 tamanhos | 100% coberto |
| Temas por página | 6 | 100% coberto |

---

## 29. Análise de Potencial de Otimização

> Dados extraídos automaticamente do codebase em 2026-03-27.
> Nenhuma das otimizações abaixo altera o visual do produto — são refatorações internas.

### 29.1 Cores Hardcoded — 298 cores hex em 1.607 linhas

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

### 29.2 Valores Arbitrários Tailwind — 4.765 ocorrências

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

### 29.3 Componentes Gigantes — 37 arquivos > 1.000 linhas = 118.037 linhas

Representam **94% de todo o código** de componentes. Cada um mistura lógica de negócio, state management, UI, e estilo. Dificulta testes, manutenção e conversão para Vue.

| # | Componente | Linhas | Categoria | Proposta de Split |
|---|-----------|--------|-----------|-----------------|
| 1 | `expanded-chat-modal` | 11.824 | Chat | → WizardChat, MessageList, InputBar, ToolResults, StageManager, StateReducer, FieldSync, JobPreview (~8-10 sub) |
| 2 | `pages/job-kanban-page` | 8.440 ✂️ | Pipeline | Sprint 4.6: KanbanFiltersPanel, KanbanColumnConfigPanel, AddColumnPopover extraídos. Pendente: KanbanBoard, CandidateCard, BulkActions, StageConfig (~4 sub) |
| 3 | `pages/candidates-page` | 9.604 ✂️ | Candidatos | Sprint 4.6: CreditConfirmationModal, SaveAsArchetypeModal, EditQueryModal, PreviewSuggestionModal extraídos. Pendente: FilterPanel, PreviewPanel, TableView, LIA inline (~4 sub) |
| 4 | `pages/jobs-page` | 4.735 ✂️ | Vagas | Sprint 4.6: ColumnConfigPanel, TableFiltersPanel, InlineChatPanel, JobPreviewPanel extraídos. Abaixo do limiar de 5.000L. |
| 5 | `candidate-preview` | 5.994 ✂️ | Candidatos | Sprint 4.6: FilePreviewModal, LiaChatModal extraídos. Pendente: Tabs de detalhe, seção de avaliação/feedback (~2-3 sub) |
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

### 29.4 Código Morto — ~7.000 linhas em 8 arquivos

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

### 29.5 Duplicação de Badges e Status — 7 componentes similares

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

### 29.6 Modais/Dialogs — 154 arquivos

154 componentes importam ou implementam Modal, Dialog, Drawer ou Sheet. Muitos reimplementam o mesmo padrão:
- Overlay com fundo escuro
- Formulário com campos
- Botões Cancel/Submit
- Validação e loading state

**Recomendação:** Criar padrão composable `FormDialog` que receba um schema de campos e gere o formulário automaticamente. Reduziria boilerplate em ~50% dos modais.

### 29.7 Inline Styles — 249 arquivos

249 dos 465 arquivos (54%) usam `style={}` inline. Problemas:
- Não responde a dark mode via classes CSS
- Não é responsivo
- Não é portável para Vue (onde scoped styles são preferidos)
- Dificulta override e customização

**Recomendação:** Converter gradualmente para classes Tailwind. Priorizar os componentes que aparecem em dark mode.

### 29.8 Resumo Quantitativo

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

## 30. Plano de Otimização em 6 Fases

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

**Esforço:** 4-6 semanas | **Risco:** Alto | **Impacto visual:** Nenhum

> **Revisão pós-análise profunda (2026-03-27):** `expanded-chat-modal.tsx` tem 76 useState,
> 30+ useEffect, 28 useCallback e 94 imports. Não é possível extrair componentes diretamente —
> o acoplamento entre estados tornaria as props impossíveis de gerenciar.
>
> **Estratégia correta:** 3 camadas sequenciais.
> Camada 1 (hooks): agrupar estados relacionados em custom hooks → reduz de 76 para ~8 objetos.
> Camada 2 (componentes simples): extrair partes sem estado próprio (risco baixo).
> Camada 3 (componentes com estado): usar hooks da Camada 1 como base (risco médio).
> **NUNCA pular camadas — cada camada é pré-requisito da próxima.**

---

#### Diagnóstico Real do `expanded-chat-modal.tsx`

| Métrica | Valor |
|---------|-------|
| Linhas totais | 11.824 |
| `useState` | 76 variáveis |
| `useRef` | 19 referências |
| `useEffect` | 30+ efeitos |
| `useCallback` | 28 funções |
| `useMemo` | 2 |
| Imports | 94 (30+ arquivos) |
| Hooks customizados importados | 18 |
| `handleSendMessage` | ~500 linhas (função monolítica) |
| Feature flag morto | `USE_MODULAR_WIZARD = false` (linha 104) |
| Efeitos duplicados | 3x lógica proativa idêntica (salary/input-eval/competencies) |

---

#### Sprint 4.1 — Extração de Tipos e Remoção de Código Morto (½ dia | Risco: Zero)

**Ações:**

| Arquivo novo | Conteúdo | Linhas extraídas |
|-------------|----------|-----------------|
| `expanded-chat-modal.types.ts` | Todas as interfaces/tipos (linhas 106–681) | ~575 |
| `expanded-chat-modal.constants.ts` | `SKILLS_CATALOG`, `ROLE_AREA_MAPPING`, `CORE_SKILLS_BY_ROLE` | ~200 |
| `expanded-chat-modal.utils.ts` | `detectAreaFromRole()`, `getSkillSuggestions()`, `inferTechnicalSkillWeight()`, `inferBehavioralSkillWeight()`, `formatTimestamp()`, `formatSalaryAnalysisText()` | ~500 |

**Remover:**
- Feature flag `USE_MODULAR_WIZARD = false` e todo código condicional associado (~100 linhas de dead code)

**Resultado:** Modal reduz de 11.824 → ~10.450 linhas. Zero risco de regressão.

---

#### Sprint 4.2 — Extração de Custom Hooks por Domínio (2-3 dias | Risco: Baixo)

> Esta é a etapa mais importante. Sem ela, extrair componentes cria prop drilling impossível.
> Cada hook agrupa estados + efeitos + callbacks de um domínio específico.

| Hook | Arquivo | States agrupados | Linhas estimadas |
|------|---------|-----------------|-----------------|
| `useSalaryState` | `hooks/wizard/use-salary-state.ts` | `salaryInfo`, `salaryBenchmark`, `isLoadingBenchmark`, `compensationAnalysis`, `salaryStageCompletionShown` | ~200 |
| `useCompetenciesState` | `hooks/wizard/use-competencies-state.ts` | `technicalSkills`, `behavioralCompetencies`, `showCompetenciesSuggestionsModal`, `suggestedTechnical/Behavioral`, `selected*`, `competenciesStageCompletionShown` | ~250 |
| `useWSIState` | `hooks/wizard/use-wsi-state.ts` | `wsiQuestions`, `wsiCandidates`, `wsiGenerationBatch`, `isGeneratingWSI`, `wsiHasGenerated`, `useCompanyQuestions`, `companyDefaultQuestions`, + geração/toggle/delete | ~300 |
| `useCalibrationState` | `hooks/wizard/use-calibration-state.ts` | `calibrationCandidates`, `currentCalibrationIndex`, `approvedCandidates`, `rejectedCandidates`, `calibrationComplete`, `isLoadingCalibration`, `showCalibrationModal`, + approve/reject handlers | ~350 |
| `useWizardNavigation` | `hooks/wizard/use-wizard-navigation.ts` | `currentStage`, `goToNextStage`, `goToPreviousStage`, `canAdvanceToNextStage`, `awaitingStageAdvanceConfirmation` | ~150 |
| `useProactiveMessages` | `hooks/wizard/use-proactive-messages.ts` | Consolida 3 useEffect idênticos (salary/input-eval/competencies) em 1 hook parametrizado | ~150 |
| `useModalStates` | `hooks/wizard/use-modal-states.ts` | Todos os `show*Modal` + inputs de formulário dos modais (15+ estados) | ~100 |
| `useJobPublishing` | `hooks/wizard/use-job-publishing.ts` | `jobConfig`, `publishingPlatforms`, `publishedJobId`, `jobDescription`, `isGeneratingDescription`, `handlePublishJob` | ~200 |

**Resultado:** Modal reduz para ~8.000 linhas. Estados viram: `salary.info`, `competencies.technical`, `wsi.questions`, etc.

**Padrão de interface de cada hook:**
```typescript
// Exemplo: useSalaryState
export function useSalaryState(currentStage: WizardStage, basicInfoFields: BasicInfoFields) {
  const [salaryInfo, setSalaryInfo] = useState<SalaryInfo>(DEFAULT_SALARY)
  const [salaryBenchmark, setSalaryBenchmark] = useState<object | null>(null)
  // ...
  return { salaryInfo, setSalaryInfo, salaryBenchmark, isLoadingBenchmark, /* handlers */ }
}
// Vue equiv: composable useSalaryState() idêntico
```

---

#### Sprint 4.3 — Extração de Componentes Sem Estado (1 dia | Risco: Baixo)

> Pré-requisito: Sprint 4.1 concluída (tipos extraídos).
> Estes componentes são puros ou quase-puros (recebem dados, não gerenciam estado).

| Componente | Arquivo | Props | Linhas estimadas |
|-----------|---------|-------|-----------------|
| `QuickSuggestionsBar` | `chat/quick-suggestions-bar.tsx` | `suggestions: string[]`, `onSelect: (s: string) => void` | ~40 |
| `ChatInput` | `chat/chat-input.tsx` | `value`, `onChange`, `onSend`, `isLoading`, `onFileSelect`, `onAudioRecord`, `inputRef` | ~120 |
| `ChatMessageItem` | `chat/chat-message-item.tsx` | `message: Message`, `isLast: boolean`, `onProactiveAccept`, `onProactiveReject` | ~200 |
| `WizardModals` | `chat/wizard-modals.tsx` | Props do `useModalStates` + handlers de submit | ~300 |
| `WizardStageHeader` | `chat/wizard-stage-header.tsx` | `currentStage`, `navigation`, `stageDisplayName` | ~80 |

**Regra:** Nenhum desses componentes chama `useState` interno — recebem tudo via props.

---

#### Sprint 4.4 — Extração de Painéis por Estágio (2 dias | Risco: Médio)

> Pré-requisito: Sprint 4.2 concluída (hooks de domínio prontos).
> Cada painel usa 1-2 hooks da Sprint 4.2 como fonte de dados.

| Componente | Arquivo | Hook base | Linhas estimadas |
|-----------|---------|-----------|-----------------|
| `SalaryStagePanel` | `wizard-stages/salary-stage-panel.tsx` | `useSalaryState` | ~400 |
| `CompetenciesStagePanel` | `wizard-stages/competencies-stage-panel.tsx` | `useCompetenciesState` | ~400 |
| `WSIQuestionsPanel` | `wizard-stages/wsi-questions-panel.tsx` | `useWSIState` | ~350 |
| `CalibrationPanel` | `wizard-stages/calibration-panel.tsx` | `useCalibrationState` | ~400 |
| `BasicInfoPanel` | `wizard-stages/basic-info-panel.tsx` | Props simples (basicInfoFields + setter) | ~250 |
| `ReviewPublishPanel` | `wizard-stages/review-publish-panel.tsx` | `useJobPublishing` | ~350 |

**Vuetify readiness:** Cada painel = 1 componente Vue futuro. Props são simples, sem React-specific patterns.

---

#### Sprint 4.5 — Refatorar `handleSendMessage` (~500 linhas → funções especializadas) (1-2 dias | Risco: Alto)

> Esta é a etapa mais arriscada. `handleSendMessage` tem 10 responsabilidades diferentes.
> Abordagem: extrair helpers sem mudar a função principal primeiro, depois decompor.

**Decomposição proposta:**
```typescript
// Funções puras extraídas (sem estado)
function buildMessagePayload(content, context): MessagePayload
function extractCriteriaFromText(text): DetectedCriteria | null
async function processOrchestratorResponse(result, messageId): ProcessedResponse

// Handlers especializados
async function handleJobCreationMessage(content, ctx): Promise<void>
async function handleGeneralChatMessage(content, ctx): Promise<void>

// handleSendMessage vira um dispatcher:
async function handleSendMessage(content) {
  if (isJobCreationMode) return handleJobCreationMessage(content, ctx)
  return handleGeneralChatMessage(content, ctx)
}
```

**Resultado final após 4.5:** Modal principal: ~2.000-2.500 linhas (orchestrador), restante distribuído em ~15 arquivos.

---

#### Sprint 4.6 — Pages Gigantes ✅ CONCLUÍDA (2026-03-28)

> **Sprint 4.6 resultado:** 13 componentes extraídos de 4 monolitos. −6.693L no total.

| Arquivo | Antes | Depois | Componentes extraídos |
|---------|-------|--------|----------------------|
| `job-kanban-page.tsx` | 10.377 | 8.440 | KanbanFiltersPanel, KanbanColumnConfigPanel, AddColumnPopover |
| `candidates-page.tsx` | 10.329 | 9.604 | CreditConfirmationModal, SaveAsArchetypeModal, EditQueryModal, PreviewSuggestionModal |
| `jobs-page.tsx` | 8.046 | 4.735 | ColumnConfigPanel, TableFiltersPanel, InlineChatPanel, JobPreviewPanel |
| `candidate-preview.tsx` | 6.723 | 5.994 | FilePreviewModal, LiaChatModal |

> **Sprint 4.7 resultado:** 8 componentes extraídos de 3 monolitos. −6.535L no total.

| Arquivo | Antes | Depois | Componentes extraídos |
|---------|-------|--------|----------------------|
| `candidates-page.tsx` | 9.604 | 8.453 | LIASearchSidebar |
| `job-kanban-page.tsx` | 8.440 | 6.308 | KanbanTableView, KanbanColumnRenderer, KanbanLIASidebar |
| `candidate-preview.tsx` | 5.994 | 2.742 | CandidateActivitiesTab, CandidateFilesTab |

> **Splits pendentes:** ver seção 22.6. Próxima sprint: Sprint 4.8 — candidates-page + expanded-chat-modal.

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

## 31. Impacto na Conversão para Vue/Vuetify

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

## 32. Tabela-Resumo do Plano

| Fase | O que faz | Resultado | Impacto visual | Risco | Esforço | Benefício Vue |
|------|----------|-----------|---------------|-------|---------|--------------|
| 0 — Limpeza ✅ | Remove código morto | 9.820 linhas removidas | Nenhum | Zero | 1 dia ✅ | Reduz ruído |
| 1 — Tipografia ✅ | text-[Xpx] → 4 tokens com CSS vars | ~4.500 valores eliminados | Nenhum | Baixo | 2 dias ✅ | Mapeamento 1:1 para Vuetify |
| 2 — Cores | 150+ hex → 15 tokens semânticos (direção monocromática) | Pipeline: 17 pastéis→4 grays; cyan: 507→200 usos | Mínimo intencional | Baixo-Médio | 6-7 dias | CSS vars sobrevivem migração Vue |
| 3 — Badges | 7 → 3 componentes | Tokens + badge.tsx como base | Nenhum | Médio | 2-3 dias | Decide componente canônico |
| 4 — Split | 37 → ~150 sub-componentes | Monólitos < 800 linhas | Nenhum | Alto | 3-4 semanas | Conversão componente a componente |
| 5 — Dimensões | px → tokens de layout | ~5.400 valores arbitrários | Mínimo | Médio | 3-5 dias | Tokens compartilhados |
| **Total** | | **~138.700** | **Zero** | | **~6-7 semanas** | **Conversão viável** |
