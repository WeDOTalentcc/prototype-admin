# Diagnóstico Completo — ats_front (Vue 3 / Vuetify 3 / Nuxt 3)

> **Data:** 2026-03-28
> **Repositório:** `wedotalent/ats_front`
> **Branch analisada:** `develop`
> **Stack:** Nuxt 3.17.5 + Vue 3.5.17 + Vuetify 3.8.11 + Pinia 2.3.1
> **Método:** Análise via GitHub API — tree completa (718 arquivos) + conteúdo dos 80 maiores .vue + amostragem 50% dos 456 menores + 100% composables/stores/config/plugins/layouts

---

## Sumário

- [Resumo Executivo](#resumo-executivo)
- [3 Problemas que Bloqueiam Conversão/Geração Automatizada](#bloco-1--3-problemas-críticos-que-bloqueiam-conversãogeração-automatizada)
- [Diagnóstico Honesto — Estado Real](#diagnóstico-honesto--estado-real)
- [Lista Completa de 37 Problemas](#lista-completa-de-37-problemas)
  - [Bloco 1 — Bloqueadores de Conversão (3)](#bloco-1--3-problemas-críticos-que-bloqueiam-conversãogeração-automatizada)
  - [Bloco 2 — Estilo e CSS (8)](#bloco-2--problemas-de-estilo-e-css-8-itens)
  - [Bloco 3 — Código e Qualidade (10)](#bloco-3--problemas-de-código-e-qualidade-10-itens)
  - [Bloco 4 — Tipagem (6)](#bloco-4--problemas-de-tipagem-6-itens)
  - [Bloco 5 — Arquitetura (7)](#bloco-5--problemas-de-arquitetura-7-itens)
  - [Bloco 6 — Infraestrutura e DX (3)](#bloco-6--problemas-de-infraestrutura-e-dx-3-itens)
- [Análise Detalhada por Categoria](#análise-detalhada-por-categoria)
- [Comparação React vs Vue](#comparação-react-plataforma-lia-vs-vue-ats_front)
- [Inventário de Branches](#inventário-de-branches-30-total)
- [Plano de Ação em Fases](#plano-de-ação-em-9-fases)
- [Roadmap Consolidado](#roadmap-consolidado)
- [Metodologia](#metodologia)

---

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| Total de arquivos no repositório | 718 |
| Arquivos `.vue` | 536 |
| Arquivos `.ts` | 105 |
| Arquivos `.js` | 4 (1 composable legado) |
| Composables (`composables/`) | 58 (57 .ts + 1 .js) |
| Stores Pinia (`stores/`) | 18 |
| Types definidos (`types/`) | 7 arquivos |
| Pages Nuxt (`pages/`) | 34 |
| Layouts (`layouts/`) | 5 |
| Plugins (`plugins/`) | 11 |
| Middleware (`middleware/`) | 1 |
| Config (`config/`) | 1 (`vuetify.config.ts`) |
| Features (`features/`) | 358 arquivos em 28 domínios |
| Components UI (`components/`) | 145 arquivos |
| CSS global (`src/assets/style.css`) | 1.864 linhas |
| Testes automatizados | **0** |
| ESLint configurado | Sim (`eslint.config.mjs` — flat config v9) |
| Prettier configurado | Sim (`.prettierrc`) |
| Tailwind CSS | **Nao usa** |
| i18n | **Nao implementado** |
| Form validation lib | **Nenhuma** |
| Error page (`error.vue`) | **Nao existe** |
| `.env.example` | **Nao existe** |

---

## Diagnóstico Honesto — Estado Real

| Item | Real (auditoria) | Status |
|------|-------------------|--------|
| Hex hardcoded (#RRGGBB) | ~50 arquivos / ~1.596 ocorrências | Nunca atacado |
| rgba() hardcoded | ~80 arquivos / ~1.350 ocorrências | Nunca atacado |
| Inline :style="" / style="" | ~220 arquivos / ~1.168 ocorrências | Problema sistêmico |
| !important em .vue | ~1.232 ocorrências estimadas | Guerra de especificidade |
| !important no style.css | 411 ocorrências em 1.864 linhas | CSS global força tudo |
| :deep() selector overrides | ~968 ocorrências estimadas | Acoplamento ao Vuetify |
| console.log/error/warn | ~60 arq Vue (~407 occ) + 58 composables (93 occ) | Nunca limpo |
| Direct axios em componentes | ~437 ocorrências estimadas (bypass $api plugin) | Sem error handling padrão |
| `: any` (composables) | 87 ocorrências / 58 composables | Moderado |
| `: any` (stores) | 28 ocorrências / 18 stores | Moderado |
| defineProps ausente | ~191/536 (36%) sem defineProps | 64% coberto |
| Dark mode | Vuetify theme OK, ~2.946 hex/rgba overridam | Infra boa, execução 0% |
| Conflito primary/cyan | CSS: primary=#60BED1, Vuetify: primary=#111827 | Confusão semântica |
| Monolitos (>500 linhas) | 35 arquivos (5 críticos >1.000 linhas) | Alto |
| Types definidos | 7 arquivos em types/ | Insuficiente |
| Testes | 0 arquivos (.test/.spec) | Zero cobertura |
| setTimeout sem cleanup | ~61 ocorrências estimadas | Memory leaks |
| setInterval em composables | 13 ocorrências | Memory leaks |
| Lifecycle cleanup ausente | ~72% sem onUnmounted pareado (top 45 files) | Memory leaks sistêmico |
| Direct window.* access | ~44 ocorrências estimadas | Quebra SSR |
| v-html (risco XSS) | ~12 ocorrências estimadas | Vulnerabilidade |
| ts-ignore / ts-nocheck | 0 ocorrências | OK |
| TODO/FIXME | ~1 ocorrência | OK |
| Composition API | 100% `<script setup>` (top 45 files) | OK |
| Scoped styles | ~92% com `<style scoped>` | OK |

---

## Lista Completa de 37 Problemas

### BLOCO 1 — 3 Problemas Críticos que Bloqueiam Conversão/Geração Automatizada

Estes 3 problemas devem ser resolvidos ANTES de qualquer esforço de conversão automatizada ou geração de código por agentes IA:

| # | Problema | Escala | Por que bloqueia |
|---|----------|--------|------------------|
| 1 | Cores hardcoded (hex + rgba) | ~2.946 ocorrências em ~130 arquivos | Qualquer ferramenta de conversão/geração precisa de tokens semânticos. Com hex/rgba inline, não há como gerar dark mode, mudar paleta, ou converter automaticamente para outro framework. |
| 2 | Zero testes automatizados | 0 arquivos .test/.spec em todo o projeto | Impossível validar que conversão/geração não quebrou funcionalidade. Cada mudança é um salto no escuro. Sem testes, não há safety net. |
| 3 | Conflito semântico primary/cyan | CSS global: primary = #60BED1; Vuetify theme: primary = #111827 | Geração automatizada não sabe qual é o "primary" real. Qualquer tool que leia o tema vai gerar output incorreto. text-primary = preto (Vuetify) vs .primary_color = cyan (CSS). |

---

### BLOCO 2 — Problemas de Estilo e CSS (8 itens)

| # | Problema | Escala | Impacto |
|---|----------|--------|---------|
| 4 | Inline styles (`:style=""`/`style=""`) | ~1.168 ocorrências / ~220 arquivos | Override do Vuetify theme, dark mode quebrado, impossível extrair para tokens. Regra: inline style legítimo APENAS para valores computados dinâmicos (ex: `:style="{ width: progress + '%' }"`). |
| 5 | !important em arquivos Vue | ~1.232 ocorrências estimadas | Guerra de especificidade CSS. Vuetify theme não consegue prevalecer. Cada !important gera necessidade de mais !important em cascata. |
| 6 | !important no style.css global | 411 ocorrências em 1.864 linhas | CSS global com !important força overrides em toda a aplicação. Qualquer componente precisa de !important para competir. |
| 7 | :deep() selector overrides | ~968 ocorrências estimadas | Acoplamento ao DOM interno do Vuetify — quebra em updates de versão. Cada upgrade do Vuetify pode mudar estrutura interna e invalidar :deep. |
| 8 | CSS global excessivo | 1.864 linhas com classes custom (.f8-.f32, .primary_color, etc.) | Classes utilitárias custom (.f8 a .f32 com !important) que duplicam funcionalidade do Vuetify. Aumentam bundle e criam confusão. |
| 9 | Unscoped `<style>` blocks | ~55 arquivos .vue com style não-scoped | Poluição do namespace CSS global. Side-effects imprevisíveis entre componentes. Estilos de um componente afetam outros. |
| 10 | Arquivos sem `<style>` | ~214 arquivos .vue | Componentes sem estilo próprio dependem de estilos globais implícitos ou herdam de parents — fragilidade e acoplamento invisível. |
| 11 | Dark mode quebrado por cores hardcoded | Vuetify theme light+dark OK, mas ~2.946 hex/rgba overridam | ~2.946 cores hardcoded impedem o tema de funcionar nos templates. Infraestrutura dark mode existe e é bem configurada, execução 0%. |

---

### BLOCO 3 — Problemas de Código e Qualidade (10 itens)

| # | Problema | Escala | Impacto |
| --- | --- | --- | --- |
| 12 | console.log/error/warn em .vue | ~407 ocorrências / ~60 arquivos | Poluição de logs de desenvolvimento. Potencial leak de informação sensível. Existe suppress-logs.client.ts mas nao resolve dev. |
| 13 | console.log em composables | 93 ocorrências / 58 composables | Mesma poluição, mas em código reutilizável — cada componente que usa o composable herda os logs. |
| 14 | Direct axios em componentes | ~437 ocorrências estimadas | Bypass do plugin $api centralizado. Sem interceptors de auth, sem error handling padrão, sem retry, sem logging uniforme. |
| 15 | setTimeout sem cleanup | ~61 ocorrências estimadas | Memory leaks quando componente desmonta antes do timeout disparar. Pode causar erros "Cannot update unmounted component". |
| 16 | setInterval em composables | 13 ocorrências em composables | Memory leaks se nao limpo em onUnmounted/onBeforeUnmount. Intervals continuam rodando após navegação de página. |
| 17 | Lifecycle cleanup ausente | onMounted sem onUnmounted pareado (~72% sem cleanup nos top 45 files) | Listeners, timers, WebSockets e subscriptions nao removidos. Memory leaks sistêmico — app fica lento com uso prolongado. |
| 18 | Direct window.* access | ~44 ocorrências estimadas | Quebra SSR do Nuxt 3. window nao existe no servidor — runtime error. Deve usar process.client guard ou <ClientOnly>. |
| 19 | v-html (risco XSS) | ~12 ocorrências estimadas (3 confirmadas + extrapolação) | Injeção de HTML nao sanitizado — vulnerabilidade de segurança. Deve usar DOMPurify ou equivalent. |
| 20 | $api plugin com `any` type | FetchContext usa options: any, request?: any, response?: any | API layer sem tipagem — erros de request/response nao sao capturados em build time. TypeScript nao protege nada. |
| 21 | Handler 401 comentado | plugins/api.ts — redirect de 401 está comentado com "// Exemplo:" | Usuário com token expirado nao é redirecionado para login. Sessão expira silenciosamente — UX degradado. |

---

### BLOCO 4 — Problemas de Tipagem (6 itens)

| # | Problema | Escala | Impacto |
| --- | --- | --- | --- |
| 22 | `: any` em composables | 87 ocorrências / 58 composables (média 1.5/composable) | Sem type safety na lógica reutilizável. Erros de runtime nao detectados em build. Qualquer valor aceito sem validação. |
| 23 | `: any` em stores | 28 ocorrências / 18 stores (média 1.6/store) | State management sem tipagem. Actions e getters aceitam qualquer tipo — bugs silenciosos em runtime. |
| 24 | defineProps ausente | ~191/536 (36%) componentes sem defineProps tipado | Componentes sem contrato de props. Impossível gerar bindings automaticamente ou validar uso correto pelo parent. |
| 25 | Types insuficientes | Apenas 7 arquivos em types/ para 536 componentes | Tipos provavelmente inline/duplicados nos composables e stores. Sem reusabilidade, sem single source of truth. |
| 26 | 1 composable em JavaScript | useActiveSection.js — legado (2.273 bytes) | Sem type checking, nao segue padrão TypeScript do projeto. Deveria ser migrado para .ts. |
| 27 | Middleware usa `: any` | microsoft-auth.ts — `(r: any)` no response do axios | Response do axios sem tipagem no middleware de auth. Erro silencioso se API mudar formato de resposta. |

---

### BLOCO 5 — Problemas de Arquitetura (7 itens)

| # | Problema | Escala | Impacto |
| --- | --- | --- | --- |
| 28 | Monolitos críticos (>1.000 lin.) | 5 arquivos: kanban.vue (2.129) lia/candidates/index.vue (2.095) jobs/form/questions.vue (1.526) evaluations/wrapper.vue (1.463) jobs/form/description.vue (1.245) | Impossível revisar, testar, ou converter individualmente. Cada arquivo contém múltiplas responsabilidades misturadas. Alto risco em qualquer mudança. |
| 29 | Monolitos altos (500-1.000 lin.) | 30 arquivos adicionais (list.vue, general.vue, settings, schedule_interview, screening, etc.) | Mesmos problemas em menor escala. Dificultam code review, onboarding de novos devs, e geração automatizada. |
| 30 | features/messages/ oversized | 88 arquivos em um único domínio | Violação de single responsibility. Difícil navegar, entender scope, e manter. Candidato a sub-modularização. |
| 31 | components/ui/table/ complexo | 52 arquivos para sistema de tabela | Subsistema que deveria ser uma lib/package separado. Acoplado ao resto da app, difícil de testar isoladamente. |
| 32 | Composables oversized | useSourcingWebSocket.ts (605 linhas) useHubVoiceCommand.ts (465 linhas) useVoiceRecorder.ts (449 linhas) useCurriculumParser.ts (417 linhas) | Composables monolíticos — difíceis de testar, manter e reutilizar. Devem ser splitados em sub-composables menores. |
| 33 | Apenas 1 middleware | Só microsoft-auth.ts Sem auth guard geral | Rotas protegidas sem guard centralizado de autenticação. Qualquer rota /user/* pode ser acessada sem token válido. |
| 34 | Sem error.vue | Nuxt error page nao implementada | Erros 404/500 mostram página default genérica do Nuxt. UX degradado para usuário final em erros. |

---

### BLOCO 6 — Problemas de Infraestrutura e DX (3 itens)

| # | Problema | Escala | Impacto |
| --- | --- | --- | --- |
| 35 | Sem .env.example | Nenhum arquivo de exemplo de env vars | Novos devs nao sabem quais variáveis configurar. Onboarding lento e propenso a erros. |
| 36 | Sem i18n | 0 ocorrências de $t(), sem vue-i18n | Todas as strings hardcoded em português. Impossível internacionalizar sem rewrite massivo. |
| 37 | Sem validação de forms padronizada | Sem VeeValidate / Zod / Yup | Cada formulário implementa validação ad-hoc ou simplesmente nao implementa. Inconsistência de UX e data quality. |

---

## Análise Detalhada por Categoria

### 1. Cores Hardcoded (Problema #1 — Bloqueador)

**Total combinado:** ~2.946 ocorrências (hex ~1.596 + rgba ~1.350) em ~130 arquivos.

#### Top offenders — Hex hardcoded (#RRGGBB):

| Arquivo | Ocorrências | Prioridade |
|---------|-------------|------------|
| `features/control_panel/event_action_dialog.vue` | 97 | Critica |
| `features/evaluations/wrapper.vue` | 88 | Critica |
| `components/ui/hub/HubVoiceOverlay.vue` | 82 | Critica |
| `features/applies/move_stage_dialog.vue` | 61 | Alta |
| `features/prompt/ExecutionTracker.vue` | 45 | Alta |
| `pages/scheduling/[account_uid]/[token].vue` | 39 | Alta |
| `features/interview/InterviewRoom.vue` | 37 | Alta |
| `features/global_search/settings/index.vue` | 33 | Alta |
| `features/lia/candidates/index.vue` | 29 | Media |
| `features/admin/accounts/credits.vue` | 26 | Media |
| `features/prompt/prompt_input.vue` | 26 | Media |
| `features/smart-calendar/SlotSelector.vue` | 26 | Media |
| `features/admin/communication/emails/editor/TemplateWYSIWYG.vue` | 19 | Media |
| `features/evaluations/VoiceRoom.vue` | 17 | Media |
| `features/lia/candidates/AddToListDialog.vue` | 17 | Media |
| `features/admin/communication/emails/ChannelPreview.vue` | 16 | Media |

#### Top offenders — rgba() hardcoded:

| Arquivo | Ocorrências | Prioridade |
|---------|-------------|------------|
| `features/applies/schedule_interview_dialog.vue` | 57 | Critica |
| `features/jobs/form/questions.vue` | 48 | Critica |
| `features/evaluations/wrapper.vue` | 47 | Critica |
| `features/interview/InterviewRoom.vue` | 44 | Critica |
| `features/applies/screening_results.vue` | 43 | Alta |
| `features/global_search/settings/index.vue` | 36 | Alta |
| `features/jobs/form/general.vue` | 32 | Alta |
| `features/admin/communication/emails/editor/TemplateWYSIWYG.vue` | 29 | Alta |
| `features/candidates/curriculum_text.vue` | 28 | Alta |
| `features/lia/jobs/search.vue` | 27 | Alta |
| `pages/evaluations/[id]/[uid].vue` | 24 | Media |
| `features/evaluations/send.vue` | 22 | Media |
| `features/applies/LiaScreeningOpinion.vue` | 22 | Media |
| `features/applies/send_interview_link_dialog.vue` | 22 | Media |
| `features/jobs/form/selective_processes.vue` | 20 | Media |
| `features/candidates/email/form.vue` | 20 | Media |

**Solução:** Substituir por Vuetify theme variables (`rgb(var(--v-theme-surface))`) ou CSS custom properties do DS definidas em `vuetify.config.ts`.

---

### 2. Inline Styles (Problema #4)

**~1.168 ocorrências** de `:style=""` ou `style=""` em ~220 arquivos.

Top offenders:

| Arquivo | Ocorrências |
|---------|-------------|
| `features/applies/schedule_interview_dialog.vue` | 13 |
| `features/lia/candidates/index.vue` | 13 |
| `features/global_search/settings/index.vue` | 11 |
| `features/applies/kanban.vue` | 8 |
| `features/applies/list.vue` | 5 |
| `features/jobs/form/questions.vue` | 4 |

**Regra:** Inline style legítimo APENAS para valores computados dinâmicos (ex: `:style="{ width: progress + '%' }"`). Todo o resto deve ser classe CSS, Vuetify utility, ou token DS.

---

### 3. !important Abuse (Problemas #5 e #6)

**Em arquivos Vue (~1.232 ocorrências estimadas):**

| Arquivo | Ocorrências |
|---------|-------------|
| `features/applies/screening_results.vue` | 56 |
| `features/global_search/settings/index.vue` | 35 |
| `features/lia/search/filters/SearchJobTitle.vue` | 32 |
| `features/lia/search/filters/SearchCompany.vue` | 29 |
| `features/applies/kanban.vue` | 17 |
| `features/jobs/form/questions.vue` | 13 |
| `features/lia/candidates/index.vue` | 8 |
| `features/applies/schedule_interview_dialog.vue` | 7 |
| `features/jobs/form/general.vue` | 3 |

**No style.css global (411 ocorrências):** Principalmente nas classes utilitárias `.f8`-`.f32`, `.primary_color`, `.primary_color_bg`, e overrides de Vuetify.

---

### 4. :deep() Selector Overrides (Problema #7)

**~968 ocorrências estimadas** de `:deep()`, `::v-deep`, ou `>>>`.

Top offenders:

| Arquivo | Ocorrências |
|---------|-------------|
| `features/lia/search/filters/SearchCompany.vue` | 35 |
| `features/lia/search/filters/SearchJobTitle.vue` | 24 |
| `features/applies/screening_results.vue` | 23 |
| `features/applies/schedule_interview_dialog.vue` | 15 |
| `features/global_search/settings/index.vue` | 12 |
| `features/evaluations/wrapper.vue` | 11 |
| `features/jobs/form/description.vue` | 8 |
| `features/jobs/form/general.vue` | 8 |
| `features/lia/candidates/index.vue` | 5 |
| `features/jobs/form/questions.vue` | 4 |

**Risco:** Cada upgrade do Vuetify pode mudar a estrutura interna dos componentes, invalidando todos os `:deep()` selectors.

---

### 5. console.log Cleanup (Problemas #12 e #13)

**Em arquivos Vue (~407 ocorrências / ~60 arquivos):**

| Arquivo | Ocorrências |
|---------|-------------|
| `features/lia/candidates/index.vue` | 31 |
| `features/lia/index.vue` | 14 |
| `features/applies/kanban.vue` | 10 |
| `features/prompt/prompt_input.vue` | 9 |
| `features/jobs/form/selective_processes.vue` | 8 |
| `features/applies/list.vue` | 7 |
| `features/jobs/form/questions.vue` | 6 |
| `features/admin/users/form.vue` | 4 |
| `features/admin/accounts/credits.vue` | 4 |
| `features/admin/users/list.vue` | 4 |
| `pages/user/candidates/index.vue` | 4 |

**Em composables (93 ocorrências / 58 composables):** Distribuídos em múltiplos composables. Nota: ESLint está configurado com `'no-console': ['warn', { allow: ['warn', 'error'] }]` mas as warnings nao estão sendo aplicadas.

---

### 6. Monolitos — Split Proposto (Problemas #28 e #29)

#### 5 Críticos (>1.000 linhas):

| Arquivo | Linhas Est. | Split Proposto |
|---------|-------------|----------------|
| `features/applies/kanban.vue` | ~2.129 | KanbanBoard, KanbanColumn, CandidateCard, BulkActions, StageConfig |
| `features/lia/candidates/index.vue` | ~2.095 | FilterPanel, ResultsList, PreviewPanel, LIAInlineActions |
| `features/jobs/form/questions.vue` | ~1.526 | QuestionList, QuestionEditor, QuestionPreview, ScoringConfig |
| `features/evaluations/wrapper.vue` | ~1.463 | EvaluationForm, ScoreDisplay, FeedbackPanel, VoiceConfig |
| `features/jobs/form/description.vue` | ~1.245 | DescriptionEditor, AIGeneratePanel, DescriptionPreview |

#### 10 Altos (700-1.000 linhas):

| Arquivo | Linhas Est. |
|---------|-------------|
| `features/applies/list.vue` | ~1.065 |
| `features/jobs/form/general.vue` | ~988 |
| `features/global_search/settings/index.vue` | ~964 |
| `features/applies/schedule_interview_dialog.vue` | ~883 |
| `features/applies/screening_results.vue` | ~843 |
| `features/lia/index.vue` | ~802 |
| `features/control_panel/event_action_dialog.vue` | ~787 |
| `features/lia/search/filters/SearchJobTitle.vue` | ~776 |
| `features/jobs/form/remuneration.vue` | ~757 |
| `features/lia/search/filters/SearchCompany.vue` | ~744 |

#### 20 Moderados (500-700 linhas):

| Arquivo | Linhas Est. |
|---------|-------------|
| `components/ui/hub/HubVoiceOverlay.vue` | ~739 |
| `features/candidates/preview.vue` | ~732 |
| `features/applies/similar_candidates_modal.vue` | ~715 |
| `features/jobs/form/screening.vue` | ~702 |
| `components/ui/table/wrapper.vue` | ~696 |
| `features/applies/move_stage_dialog.vue` | ~696 |
| `features/lia/search/side-panel.vue` | ~677 |
| `pages/user/jobs/index.vue` | ~675 |
| `pages/terms.vue` | ~659 |
| `features/smart-calendar/SmartCalendarDialog.vue` | ~655 |
| `features/evaluations/send.vue` | ~649 |
| `features/candidates/cards/score_analysis.vue` | ~608 |
| `pages/vagas/[slug]/[account_slug].vue` | ~577 |
| `components/ui/base/BaseChip.story.vue` | ~576 |
| `features/evaluations/form.vue` | ~574 |
| `pages/evaluations/[id]/[uid].vue` | ~569 |
| `features/jobs/form/selective_processes.vue` | ~547 |
| `features/lia/candidates/results.vue` | ~542 |
| `features/applies/LiaScreeningOpinion.vue` | ~538 |
| `pages/user/microsoft.vue` | ~529 |

#### 4 Composables oversized (Problema #32):

| Composable | Linhas | Split Proposto |
|------------|--------|----------------|
| `useSourcingWebSocket.ts` | 605 | useWebSocketConnection + useSourcingState + useSourcingActions |
| `useHubVoiceCommand.ts` | 465 | useVoiceRecognition + useHubActions + useVoiceUI |
| `useVoiceRecorder.ts` | 449 | useAudioCapture + useAudioProcessing + useRecorderState |
| `useCurriculumParser.ts` | 417 | useFileParser + useFieldExtractor + useParserValidation |

---

### 7. Tipagem e Type Safety (Problemas #22-#27)

**Composables (58 arquivos, 8.916 linhas):**
- `: any` — **87 ocorrências** (média 1.5/composable)
- 57 em TypeScript, 1 em JavaScript (`useActiveSection.js` — legado)
- `ts-ignore`/`ts-nocheck` — 0 (bom)
- 31 composables com >100 linhas

**Stores (18 arquivos, 1.569 linhas):**
- `: any` — **28 ocorrências** (média 1.6/store)
- Maior: `stores/table.ts` com 462 linhas (monolito de store)
- Stores com `any`: `table.ts`, `searchCredits.ts`, `sourcingFilters.ts`, `benefit.ts`, `candidate_feedbacks.ts`

**Types (7 arquivos em types/):**
- `communication-template.ts` (2.361 bytes)
- `execution-tracking.ts` (830 bytes)
- `interview.ts` (1.001 bytes)
- `llm-quota.ts` (2.119 bytes)
- `sector.ts` (1.179 bytes)
- `smart-calendar.ts` (1.720 bytes)
- `actioncable.d.ts` (158 bytes — ambient)

**Diagnóstico:** 7 arquivos de tipos para 536 componentes + 58 composables + 18 stores é **gravemente insuficiente**. Muitos tipos estão inline nos composables/stores ou simplesmente nao existem (`: any`).

**defineProps tipadas:**
- ~345 de 536 componentes (64%) usam `defineProps`
- ~191 (36%) sem `defineProps` — provavelmente componentes sem props ou usando `$attrs` implícito

---

### 8. Dark Mode (Problema #11)

**Infraestrutura (BEM configurada):**
- `config/vuetify.config.ts` — tema light e dark completo com TODAS as cores WeDo:
  - Surface: `background`, `on-background`, `surface`, `on-surface`, `surface-variant`
  - Primary: `#111827` (light) / `#F9FAFB` (dark)
  - WeDo accents: `wedo-cyan`, `wedo-green`, `wedo-orange`, `wedo-purple`, `wedo-magenta`
  - Semânticos: `error`, `warning`, `info`, `success`
  - Text: `body`, `body-light`, `body-lighter`, `body-disabled`, `heading`
- `plugins/vuetify.ts` — carrega tema do localStorage (`app-theme-preference`)
- Component defaults: `VBtn rounded 12px`, `VTextField density compact`

**Execução (ZERO):**
- O Vuetify theme funciona automaticamente para componentes Vuetify (`v-btn`, `v-card`, `v-dialog`...)
- Porém: **~2.946 ocorrências de hex/rgba hardcoded** nos templates Vue **overridam o dark mode**
- Classes CSS custom (`.f8`, `.f12`, etc.) em `style.css` nao têm variantes dark
- Apenas ~2 de 536 arquivos .vue usam classes `dark:` explícitas
- **O dark mode "funciona" para Vuetify components mas FALHA para qualquer estilo custom**

---

### 9. Conflito Primary/Cyan (Problema #3 — Bloqueador)

**O que acontece:**

```css
/* src/assets/style.css (CSS global) */
:root {
  --v-primary: #60BED1;  /* WeDo cyan como "primary" */
}
.primary_color { color: var(--v-primary); }  /* cyan */
.primary_color_bg { background-color: var(--v-primary) !important; }  /* cyan */
```

```typescript
/* config/vuetify.config.ts (Vuetify theme) */
export const lightTheme = {
  colors: {
    primary: '#111827',  /* Gray 900 = preto como "primary" */
  }
}
```

**Resultado:**
- `class="text-primary"` → preto (Vuetify)
- `class="primary_color"` → cyan (CSS global)
- Ambos dizem "primary" mas apontam para cores completamente diferentes
- Qualquer ferramenta de geração automatizada que leia "primary" vai produzir output errado

**Solução:** Unificar. O Vuetify theme (primary = #111827) é o padrão do DS v4.1. O CSS global deve ser atualizado para usar `wedo-cyan` em vez de `--v-primary` para a cor #60BED1.

---

### 10. Arquitetura e Estrutura

#### Estrutura de Diretórios:

```
ats_front/
  app.vue                          # Root: v-app > v-main > NuxtLayout > NuxtPage
  nuxt.config.ts                   # 67 linhas, Vuetify + Pinia
  config/
    vuetify.config.ts              # Light/dark themes + component defaults
  plugins/                         # 11 plugins
    api.ts                         # $api provider (fetch-based)
    axios.ts                       # axios instance
    vuetify.ts                     # Vuetify setup
    suppress-logs.client.ts        # Console log suppression
    toast.client.ts                # Vue-toastification
    vue-flow.ts                    # Vue Flow diagrams
    vue-tel-input.client.ts        # Phone input
    vue-the-mask.client.ts         # Input masking
    auto-animate.client.ts         # @formkit/auto-animate
    register-table-cells.ts        # Table cell components
    websocket.client.ts            # WebSocket setup
  middleware/
    microsoft-auth.ts              # Unico middleware (Microsoft Graph)
  layouts/
    user.vue                       # Layout principal autenticado (Sidebar + Menu + Splitpanes)
    admin.vue                      # Layout admin
    evaluations.vue                # Layout avaliacoes
    setup.vue                      # Layout setup
    blank.vue                      # Layout vazio
  pages/                           # 34 rotas Nuxt 3
  features/                        # 358 arquivos em 28 dominios
  components/
    ui/                            # 145 componentes compartilhados
      table/                       # 52 arquivos (subsistema de tabela)
      base/                        # 22 arquivos (BaseChip, BaseInput, etc.)
      form/                        # 15 arquivos
      chat/                        # 10 arquivos
      menu/                        # 4 arquivos (sidebar.vue, menu.vue)
      ...
    shared/                        # 3 componentes
    sourcing/                      # 3 componentes
    llm/                           # 8 componentes
    applies/                       # 1 componente
  composables/                     # 58 composables (57 .ts + 1 .js)
  stores/                          # 18 stores Pinia
  types/                           # 7 arquivos de tipos
  src/assets/
    style.css                      # 1.864 linhas CSS global
  public/                          # Assets estáticos
```

#### Features por domínio:

| Domínio | Arquivos | Observação |
|---------|----------|------------|
| `features/messages/` | 88 | MAIOR — candidato a sub-modularização |
| `features/candidates/` | 48 | |
| `features/lia/` | 46 | Inclui chat, search, candidates |
| `features/admin/` | 44 | Users, accounts, communication, sectors, etc. |
| `features/jobs/` | 38 | Forms (description, general, questions, etc.) |
| `features/applies/` | 23 | Kanban, list, screening, dialogs |
| `features/evaluations/` | 8 | Wrapper, form, send, VoiceRoom |
| `features/activity_logs/` | 7 | |
| `features/setups/` | 6 | |
| `features/benefits/` | 5 | |
| `features/interview/` | 5 | InterviewRoom |
| `features/prompt/` | 5 | ExecutionTracker, prompt_input |
| `features/questions/` | 5 | |
| `features/control_panel/` | 4 | event_action_dialog |
| `features/selective_process/` | 4 | |
| `features/smart-calendar/` | 4 | SmartCalendarDialog, SlotSelector |
| `features/addresses/` | 3 | |
| `features/feedbacks/` | 2 | |
| `features/languages/` | 2 | |
| `features/remunerations/` | 2 | |
| `features/skills/` | 2 | |
| `features/businesses/` | 1 | |
| `features/entity_columns/` | 1 | |
| `features/filters/` | 1 | |
| `features/global_search/` | 1 | settings/index.vue (964 linhas) |
| `features/job_status/` | 1 | |
| `features/organizational_structure/` | 1 | |
| `features/talent_pool/` | 1 | |

#### Pontos positivos:
- 100% Composition API (`<script setup>`)
- 58 composables bem nomeados (padrão `use*`)
- 18 stores Pinia com separação de concerns
- Vuetify config centralizada com DS v4.1
- Layouts separados por contexto
- ESLint + Prettier configurados
- 0 ts-ignore / 0 ts-nocheck
- Fontes do DS: Open Sans + Inter + Source Serif 4

---

### 11. Design System

**Vuetify Theme Config (DS v4.1) — BEM implementado:**

Light Theme:
- `background: #f9fafb` / `surface: #ffffff`
- `primary: #111827` (Gray 900 — botoes pretos)
- `secondary: #E5E7EB`
- WeDo accents: `wedo-cyan: #60BED1`, `wedo-green: #5DA47A`, `wedo-orange: #D19960`, `wedo-purple: #9860D1`, `wedo-magenta: #D160AB`
- Semânticos: `error: #EF4444`, `warning: #F59E0B`, `info: #3B82F6`, `success: #22C55E`
- Text hierarchy: `heading: #111827`, `body: #1F2937`, `body-light: #4B5563`, `body-lighter: #6B7280`, `body-disabled: #9CA3AF`

Dark Theme:
- `background: #1A1D1F` / `surface: #0F1113`
- `primary: #F9FAFB` (invertido)
- WeDo accents: tons mais escuros (`wedo-cyan: #4DA8BB`, etc.)
- Text hierarchy invertida: `heading: #F9FAFB`, `body: #E5E7EB`

Component Defaults:
- `VBtn: rounded 12px, font-weight-medium, text-none`
- `VTextField: rounded 12px, density compact`
- `VSelect: density compact, menu offset 4`
- `VList/VListItem: density compact`

**CSS Global (style.css) — Problemas:**
- 1.864 linhas com 411 `!important`
- Fontes importadas via Google Fonts: Open Sans, Inter, Source Serif 4
- Classes tipográficas custom: `.wedo-display`, `.wedo-heading-*`, `.wedo-label`, `.wedo-body-*`
- Classes de tamanho fixo `.f8` a `.f32` com `!important`
- `:root` define `--v-primary: #60BED1` — CONFLITA com Vuetify primary
- Classes `.primary_color` e `.primary_color_bg` usam cyan como "primary"

---

### 12. Dependencies e Infraestrutura

#### Dependências principais:

| Dependência | Versão | Status |
|-------------|--------|--------|
| Vue | ^3.5.17 | Atual |
| Nuxt | ^3.17.5 | Atual |
| Vuetify | ^3.8.11 | Atual |
| Pinia | ^2.3.1 | Atual |
| @pinia/nuxt | ^0.4.11 | Atual |
| Axios | ^1.10.0 | Atual |
| ESLint | ^9.37.0 | Atual (flat config) |
| Prettier | ^3.8.1 | Atual |
| @mdi/font | ^7.4.47 | Atual (Material Design Icons) |

#### Dependências ausentes notáveis:

| Lib | Categoria | Impacto |
|-----|-----------|---------|
| Vitest | Testes unitários | Zero testes |
| @vue/test-utils | Testes de componentes | Zero testes |
| Playwright/Cypress | Testes E2E | Zero testes |
| VeeValidate | Validação de forms | Validação ad-hoc |
| Zod / Yup | Schema validation | Sem validação tipada |
| vue-i18n / @nuxtjs/i18n | Internacionalização | Strings hardcoded |
| DOMPurify | Sanitização HTML | v-html sem proteção |

#### Plugins instalados (11):

| Plugin | Tipo | Observação |
|--------|------|------------|
| `api.ts` | Server | $api provider — handler 401 comentado |
| `axios.ts` | Server | Axios instance separado do $api |
| `vuetify.ts` | Server | Setup Vuetify com themes + defaults |
| `suppress-logs.client.ts` | Client | Suprime console.log em produção |
| `toast.client.ts` | Client | Vue-toastification |
| `vue-flow.ts` | Server | Vue Flow para diagramas |
| `vue-tel-input.client.ts` | Client | Input de telefone |
| `vue-the-mask.client.ts` | Client | Input masking |
| `auto-animate.client.ts` | Client | @formkit/auto-animate |
| `register-table-cells.ts` | Server | Registro de componentes de tabela |
| `websocket.client.ts` | Client | ActionCable WebSocket setup |

---

## Comparação React (plataforma-lia) vs Vue (ats_front)

| Dimensão | plataforma-lia (React) | ats_front (Vue) | Veredito |
|----------|----------------------|-----------------|----------|
| **Inline styles** | 221 arq / 2.226 occ | ~220 arq / ~1.168 occ | Vue 2x melhor |
| **Hex hardcoded** | 12 arq / 137 occ | ~50 arq / ~1.596 occ | React 12x melhor |
| **rgba() hardcoded** | 47 arq / 241 occ | ~80 arq / ~1.350 occ | React 6x melhor |
| **console.log** | 15 arq / 200+ occ | ~60 arq / ~500 occ (vue+composables) | React 2.5x melhor |
| **`: any` type** | 207 occ (top 4 files) | ~129 occ (composables+stores+vue) | React pior |
| **Props tipadas** | 502/504 sem interface | ~191/536 sem defineProps (36%) | Vue muito melhor |
| **Dark mode** | 440/504 sem dark: | Vuetify auto-theme + ~2.946 hex overridam | Vue infra melhor, execucao pior |
| **!important** | Nao medido | ~1.643 (1.232 vue + 411 css) | Vue tem problema grave |
| **:deep() selectors** | N/A (React nao tem) | ~968 ocorrências | Problema exclusivo Vue |
| **Monolitos** | 5 críticos (4-5k linhas) | 5 críticos (1.2-2.1k linhas) | Vue monolitos menores |
| **Testes** | Parcial | **Zero** | React melhor |
| **Composables/hooks** | ~30+ hooks | 58 composables | Vue mais modular |
| **State management** | Context API | 18 Pinia stores | Vue mais organizado |
| **Arquitetura** | Flat components/ | features/ + components/ | Vue melhor estrutura |
| **API layer** | Axios direto | $api plugin (mas bypass) | Similar |
| **CSS framework** | Tailwind CSS + tokens CSS | Vuetify utilities + CSS custom | Abordagens diferentes |
| **DS implementado** | DS v4.2.1 em CSS vars | DS v4.1 em Vuetify theme | Vue centralizado, conflito primary |
| **Form validation** | Nao padronizado | Nao padronizado | Ambos deficientes |
| **i18n** | Nao implementado | Nao implementado | Ambos ausentes |
| **Error page** | Existe | Nao existe | React melhor |

---

## Inventário de Branches (30 total)

| Categoria | Branch | Observação |
|-----------|--------|------------|
| **Produção** | `main` | Branch de deploy |
| **Desenvolvimento** | `develop` | Branch principal dev (ANALISADA) |
| **Legado** | `master` | Provavelmente deprecado |
| **Legado** | `paulo` | 16 commits atrás de develop, 0 à frente. SEM código exclusivo. |
| **Design System** | `design_system_1.0` | Branch do DS |
| **Victhor** | `develop_victhor` | Branch dev do Victhor |
| **Victhor** | `load_victhor` | Branch de carga do Victhor |
| **Felipe** | `develop-felipe_allow-to-receive-prompt-messages-in-apply-prompt` | Feature: prompt messages |
| **Felipe** | `develop-felipe_fix-move-stage-dialog-autocomplete-and-fields-design` | Fix: move stage dialog |
| **Felipe** | `develop-felipe_refactor-job-description-section-of-job-forms` | Refactor: job description |
| **Giovanni** | `develop-giovanni_WYSIWYG-template-editor` | Feature: editor WYSIWYG |
| **Giovanni** | `develop-giovanni_advanced-filters` | Feature: filtros avançados |
| **Giovanni** | `develop-giovanni_agt-details` | Feature: detalhes AGT |
| **Giovanni** | `develop-giovanni_badge-score-wsi` | Feature: badge WSI |
| **Giovanni** | `develop-giovanni_modal-reject` | Feature: modal reject |
| **Giovanni** | `develop-giovanni_public-chat` | Feature: chat público |
| **Giovanni** | `develop-giovanni_public-chat-triage` | Feature: triage chat |
| **Cursor** | `cursor/evaluation-completion-websocket-url-3f86` | Fix: WebSocket URL |
| **Outros** | `archetypes` | Feature: archetypes |
| **Outros** | `smart-prompt` | Feature: smart prompt |
| **Jira** | `WT-1592` | Ticket Jira |
| **Jira** | `WT-1598` | Ticket Jira |
| **Jira** | `WT-1600` | Ticket Jira |
| **Jira** | `WT-1605` | Ticket Jira |
| **Jira** | `WT-1606` | Ticket Jira |
| **Jira** | `WT-1608` | Ticket Jira |
| **Jira** | `WT-1610` | Ticket Jira |
| **Jira** | `WT-1611` | Ticket Jira |
| **Jira** | `WT-1631` | Ticket Jira |
| **Jira** | `WT-1722` | Ticket Jira |

**Branches candidatas a limpeza:**
- `paulo` — 16 commits atrás, 0 exclusivos, pode ser deletada
- `master` — branch legada se `main` é a branch de produção
- `develop_victhor` / `load_victhor` — verificar se ainda ativas

---

## Plano de Ação em 9 Fases

### Fase A — Cleanup Imediato [sem risco] [2 agentes paralelos]

**Estimativa: 1 sprint**

| # | Ação | Arquivos | Agente |
| --- | --- | --- | --- |
| A1 | Remover console.log/error/warn em .vue | ~60 arquivos / ~407 ocorrências | Agente 1 |
| A2 | Remover console.log em composables | 58 composables / 93 ocorrências | Agente 1 |
| A3 | Migrar useActiveSection.js para .ts | 1 arquivo | Agente 1 |
| A4 | Criar error.vue (Nuxt error page) | 1 arquivo novo | Agente 2 |
| A5 | Criar .env.example | 1 arquivo novo | Agente 2 |
| A6 | Fix handler 401 em plugins/api.ts | 1 arquivo | Agente 2 |
| A7 | Resolver conflito primary/cyan no style.css | 1 arquivo (style.css) | Agente 2 |

---

### Fase B — Color Tokens [baixo risco] [2 agentes paralelos]

**Estimativa: 2 sprints — 2.946 ocorrências / ~130 arquivos**

Agente 1 — Hex hardcoded (~1.596 ocorrências / ~50 arquivos):

| Arquivo | Ocorrências | Prioridade |
|---------|-------------|------------|
| `control_panel/event_action_dialog.vue` | 97 | Critica |
| `evaluations/wrapper.vue` | 88 | Critica |
| `ui/hub/HubVoiceOverlay.vue` | 82 | Critica |
| `applies/move_stage_dialog.vue` | 61 | Alta |
| `prompt/ExecutionTracker.vue` | 45 | Alta |
| + 45 arquivos | ~1.223 | Media-Baixa |

Agente 2 — rgba() hardcoded (~1.350 ocorrências / ~80 arquivos):

| Arquivo | Ocorrências | Prioridade |
|---------|-------------|------------|
| `applies/schedule_interview_dialog.vue` | 57 | Critica |
| `jobs/form/questions.vue` | 48 | Critica |
| `evaluations/wrapper.vue` | 47 | Critica |
| `interview/InterviewRoom.vue` | 44 | Critica |
| `applies/screening_results.vue` | 43 | Alta |
| + 75 arquivos | ~1.111 | Media-Baixa |

**Exceção legítima:** backgrounds de badges/chips com rgba(wedo-color, 0.1/0.15) — substituir por tokens `bg-wedo-cyan-light` definidos no Vuetify theme.

---

### Fase C — Type Safety [médio risco] [3 agentes paralelos]

**Estimativa: 2 sprints**

Agente 1 — `: any` em composables (87 ocorrências):
- Criar interfaces tipadas para os top composables
- Priorizar: `useSourcingWebSocket.ts`, `useHubVoiceCommand.ts`, `useCandidateFilters.ts`

Agente 2 — `: any` em stores (28 ocorrências) + types/:
- Tipar as 18 stores Pinia
- Expandir types/ de 7 para ~20+ arquivos compartilhados
- Priorizar: `table.ts` (462 linhas, monolito de store)

Agente 3 — defineProps nos 191 componentes sem tipagem:
- Aplicar defineProps tipado nos componentes que recebem props via `$attrs`
- Priorizar arquivos que serao splitados nas Fases D/E

**defineProps tipadas sao pré-requisito para geração automatizada.**

---

### Fase D — Monolith Split [alto risco] [2 agentes paralelos]

**Estimativa: 3 sprints**

Sprint D.1 — Top 2 críticos:

| Arquivo | Linhas | Split proposto |
|---------|--------|----------------|
| `features/applies/kanban.vue` | ~2.129 | KanbanBoard, KanbanColumn, CandidateCard, BulkActions, StageConfig (~5 sub) |
| `features/lia/candidates/index.vue` | ~2.095 | FilterPanel, ResultsList, PreviewPanel, LIAInlineActions (~4 sub) |

Sprint D.2 — Próximos 3 críticos:

| Arquivo | Linhas | Split proposto |
|---------|--------|----------------|
| `features/jobs/form/questions.vue` | ~1.526 | QuestionList, QuestionEditor, QuestionPreview, ScoringConfig |
| `features/evaluations/wrapper.vue` | ~1.463 | EvaluationForm, ScoreDisplay, FeedbackPanel, VoiceConfig |
| `features/jobs/form/description.vue` | ~1.245 | DescriptionEditor, AIGeneratePanel, DescriptionPreview |

Sprint D.3 — Altos residuais (top 10 de 500-1.000 linhas):

| Arquivo | Linhas |
|---------|--------|
| `features/applies/list.vue` | ~1.065 |
| `features/jobs/form/general.vue` | ~988 |
| `features/global_search/settings/index.vue` | ~964 |
| `features/applies/schedule_interview_dialog.vue` | ~883 |
| `features/applies/screening_results.vue` | ~843 |
| `features/lia/index.vue` | ~802 |

---

### Fase E — CSS Cleanup [médio risco] [3 agentes paralelos]

**Estimativa: 2 sprints**

Agente 1 — Inline styles (~1.168 ocorrências / ~220 arquivos):
- Converter `:style=""` para classes Vuetify ou CSS scoped
- Manter apenas inline styles para valores computados dinâmicos

Agente 2 — !important (~1.643 ocorrências total):
- Remover !important em .vue files (~1.232 occ)
- Refatorar style.css (~411 occ) — usar especificidade correta
- Reduzir style.css de 1.864 para ~500 linhas

Agente 3 — :deep() selectors (~968 ocorrências):
- Avaliar quais sao necessários vs quais podem usar component defaults do Vuetify
- Documentar os necessários como "technical debt aceito"
- Priorizar remoção dos que tocam classes internas instáveis

---

### Fase F — Lifecycle e Memory Leaks [médio risco] [2 agentes paralelos]

**Estimativa: 1 sprint**

Agente 1 — setTimeout/setInterval cleanup:
- ~61 setTimeout + 13 setInterval sem clearTimeout/clearInterval
- Adicionar onBeforeUnmount para cada timer

Agente 2 — addEventListener/window.* + SSR:
- ~44 window.* diretos — wrap com process.client ou useNuxtApp()
- Verificar addEventListener sem removeEventListener pareado
- Audit v-html (~12 occ) — adicionar DOMPurify onde necessário

---

### Fase G — API Layer Consolidation [baixo risco] [1 agente]

**Estimativa: 1 sprint**

- Consolidar ~437 usos diretos de axios para usar $api plugin
- Tipar FetchContext no plugins/api.ts (remover `any`)
- Implementar handler 401 (descomentar e completar)
- Adicionar middleware auth guard geral para rotas /user/*

---

### Fase H — Testes [médio risco] [3 agentes paralelos]

**Estimativa: 2 sprints**

Agente 1 — Setup + composables:
- Instalar Vitest + @vue/test-utils
- Testes para os 10 composables mais usados
- Priorizar: `useCandidateFilters`, `useFormatter`, `useLlmQuota`

Agente 2 — Stores + API:
- Testes para as 5 stores mais críticas
- Testes para o plugin $api
- Priorizar: `table.ts`, `searchCredits.ts`, `user.ts`

Agente 3 — Componentes + E2E:
- Instalar Playwright
- Testes E2E para os 5 fluxos principais (login, job creation, kanban, candidates, evaluations)

---

### Fase I — Auditoria Final [sem risco] [3 agentes paralelos]

**Estimativa: 1 sprint**

| Dimensões | Agente |
| --- | --- |
| D1-D5: Tokens, DS v4.1, dark mode, tipografia, espaçamento | Agente 1 |
| D6-D10: Vue portability, type safety, composables, props, stores | Agente 2 |
| D11-D14: Performance, acessibilidade (WCAG), compliance LGPD, testes | Agente 3 |

---

## Roadmap Consolidado

```
Fase A  ████░ Cleanup imediato              1 sprint   Risco: zero
Fase B  █████████░ Color tokens             2 sprints  Risco: baixo
Fase C  █████████░ Type Safety              2 sprints  Risco: medio
Fase D  ████████████████░ Monolith split    3 sprints  Risco: alto
Fase E  █████████░ CSS Cleanup              2 sprints  Risco: medio
Fase F  ████░ Lifecycle / Memory Leaks      1 sprint   Risco: medio
Fase G  ████░ API Layer Consolidation       1 sprint   Risco: baixo
Fase H  █████████░ Testes                   2 sprints  Risco: medio
Fase I  ████░ Auditoria final               1 sprint   Risco: zero
        ─────────────────────────────────────────
        Total: ~15 sprints
```

**Dependências entre fases:**
- Fase A (cleanup) deve ser feita primeiro — remove ruído para as próximas
- Fase B (color tokens) desbloqueia Fase E (CSS cleanup) e dark mode funcional
- Fase C (type safety) desbloqueia Fase D (monolith split) — precisa de props tipadas antes de splittar
- Fase D (split) deve preceder Fase H (testes) — testar componentes menores é mais efetivo
- Fase F e G podem rodar em paralelo com B/C
- Fase I é sempre a última — validação final

---

## Metodologia

- **Tree completa:** 718 arquivos mapeados via `git/trees/develop?recursive=1`
- **Análise direta (conteúdo):** 80 maiores .vue files via Contents API (linha a linha)
- **Amostragem representativa:** 228 de 456 pequenos .vue files (50% sampling, extrapolado com fator 2.0x)
- **100% cobertura em infra:** Todos os 58 composables + 18 stores + 7 types + 11 plugins + 5 layouts + 1 middleware + config
- **Padrões adicionais:** 45 maiores .vue files analisados para v-html, !important, :deep(), setTimeout, axios direto, window.*, lifecycle cleanup, script setup vs options API
- **Amostras menores:** 62 de 491 pequenos files (sampling 1-em-8) para projeção de padrões
- **Limitação:** Contagens sao estimativas baseadas em regex patterns, nao AST parsing. Margem de erro: ±15% para extrapolações, ±5% para análise direta.
- **Data:** 2026-03-28. Branch: `develop` (SHA atual).
