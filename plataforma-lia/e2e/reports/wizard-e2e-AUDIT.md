# Wizard E2E — AUDIT (Fase 1, sem código)

**Data:** 2026-04-29
**Escopo:** auditoria de selectors, fixtures e gaps antes de escrever specs Playwright para os 7 cenários A–G do wizard de criação de vagas.
**Modo:** read-only — nenhum arquivo `.tsx`/`.ts` de produção tocado, nenhum spec criado.

---

## TL;DR — Recomendação geral

> **Produto precisa de mais investimento em wiring antes de E2E robusto dos 7 cenários.**

Os 3 painéis nominais do brief (`WizardJDReviewPanel`, `WizardWSIListPanel`, `WizardCalibrationPanel`) **existem como dead code** — vivem em `src/components/unified-chat/wizard/panels/` mas têm **zero callers** em todo `src/`. O renderizador real (`DynamicContextPanel`) importa **outros** painéis (`ReviewPanel`, `WsiQuestionsPanel`, `CalibrationPanel`, sem o prefixo `Wizard`).

Igualmente, `PromptSuggestionsPanel.workflowContext` (chips contextuais "Iniciar triagem") tem **zero callers** que passem a prop — chips estão definidos mas nunca renderizados.

**Implicação:** os cenários A–D dependem de painéis que não estão em tela; F depende do `WizardCalibrationPanel` morto; G depende de chips que ninguém renderiza. Cenário E (validators / missing_fields) é o único parcialmente cobrível com a UI atual. Adicionar 5 testids não conserta isso — **precisa wirar primeiro**, depois testar.

Faixa: **0 testids justificáveis nesta fase**. Recomendo abrir 3 issues de produto antes da Fase 2.

---

## Seção 1 — Selectors reais por elemento do wizard

Convenção: `file:linha` referencia o JSX que rende cada elemento. Selectors recomendados em **negrito**.

### Container do chat unificado
- `src/components/unified-chat/UnifiedChat.tsx:616` — único `data-testid` no componente é `wizard-progress-bar` (sticky bar, só aparece quando `wizardActive`). O container raiz não tem testid próprio.
- **Recomendado:** `[data-testid="wizard-progress-bar"]` quando o wizard estiver ativo, ou ancorar via `[data-testid="lia-bubble"]` (botão flutuante, sempre presente — ver `UnifiedChatBubble.tsx:226`).
- Não há `[data-testid="unified-chat"]` em nenhum lugar.

### Textarea de mensagem
- `src/components/unified-chat/UnifiedChatInput.tsx:157-173` — `<textarea>` com `placeholder={t('placeholder')}` (i18n) e `aria-label={t('messageLabel')}`.
- **Recomendado:** `page.getByRole('textbox', { name: /mensagem|message/i })` (acessível, locale-agnostic) ou `textarea[aria-label]:not([aria-hidden])`.
- Placeholder real depende do idioma carregado por `next-intl` — **NÃO** assumir literal `"Faça qualquer coisa com a LIA..."` (não existe no source).

### Botão de enviar mensagem
- `src/components/unified-chat/UnifiedChatInput.tsx:285-302` — botão com `aria-label={t('sendLabel')}`, ícone `<Send>` ou `<Loader2>` quando `isBusy`.
- **Recomendado:** `page.getByRole('button', { name: t('sendLabel') })` ou fallback `button:has(svg.lucide-send)`.
- Atalho preferido: `chatInput.press('Enter')` (handler em `UnifiedChatInput.tsx:63-68`, `Enter` sem `Shift` chama `onSend`).

### Última mensagem da LIA (bubble)
- `src/components/unified-chat/UnifiedMessageList.tsx:289-345` — flag interna `isLia = message.sender === "lia"`, mas **nenhum `data-testid` ou `data-author`** é emitido. A diferença visual é `className: isLia ? "" : "flex justify-end"` no wrapper.
- A única classe estável e identificadora é **`.lia-markdown-content`** (linha 327, dentro do JSX da bubble da LIA). Mensagens do usuário não têm essa classe.
- **Recomendado:** `page.locator('.lia-markdown-content').last()`.
- `UnifiedChatBubble.tsx:226` tem `data-testid="lia-bubble"` mas isso é o **botão flutuante**, não a mensagem.
- `lia-expanded-panel.tsx:425,461` tem `data-testid="chat-message"` mas isso é em **outro componente** (painel expandido legacy), não o chat principal.

### Última mensagem do usuário
- Mesmo lugar — bloco no `else` do `isLia` (linha 308: `"flex justify-end"`).
- **Recomendado:** `page.locator('div.flex.justify-end').last()` ou contar bubbles e pegar índice. Sem testid, é frágil.

### Indicador de stage atual do wizard
- `[data-testid="wizard-progress-bar"]` em `UnifiedChat.tsx:616` é o container. O conteúdo interno (qual stage está ativo, quanto progresso) vem de `<WizardProgressBar>` — não inspecionei o detalhe do testid interno.
- **Recomendado:** `[data-testid="wizard-progress-bar"]` para visibilidade; para extrair stage, fazer text match dentro do progressbar (frágil) ou interceptar o WS message `wizard_stage`.

### Painel `WizardJDReviewPanel`
- `src/components/unified-chat/wizard/panels/WizardJDReviewPanel.tsx:118` — `<div className="flex flex-col h-full">` raiz, **sem `data-testid` e sem className única**. Botão `Aceitar` em `:190-197`.
- **CRÍTICO:** zero callers em `src/`. Não está montado em lugar nenhum. Selector é irrelevante.
- O painel realmente usado para review é **`ReviewPanel`** (importado em `DynamicContextPanel.tsx:32` do file `panels/ReviewPanel.tsx`).

### Painel `WizardWSIListPanel`
- `src/components/unified-chat/wizard/panels/WizardWSIListPanel.tsx:208-267` — root `<div className="flex flex-col h-full">`, sem `data-testid`. Botão `Aceitar selecionadas` em `:257-264`.
- **CRÍTICO:** zero callers. Painel real é **`WsiQuestionsPanel`** (`DynamicContextPanel.tsx:26`).

### Painel `WizardCalibrationPanel`
- `src/components/unified-chat/wizard/panels/WizardCalibrationPanel.tsx:180-251` — root `<div className="flex flex-col h-full">`, sem `data-testid`. Botão "Finalizar Calibração" em `:242-247`. CandidateCard em `:91-157` com botões `aria-label="Aprovar/Rejeitar ${name}"`.
- **CRÍTICO:** zero callers. Painel real é **`CalibrationPanel`** (`DynamicContextPanel.tsx:38`).

### Card pipeline template (5 tiles)
- `src/components/unified-chat/wizard/WizardPipelineTemplateCard.tsx:73-77` — root tem `data-testid="wizard-template-card"` ✅.
- Cada tile (linha 99-100): `data-testid="wizard-template-option-${option.id}"` + `data-suggested="true"` no tile sugerido.
- **Recomendado para Cenários A-D:**
  - `page.locator('[data-testid="wizard-template-card"]')` — container
  - `page.locator('[data-testid="wizard-template-option-technical"]')` — tile técnico
  - `page.locator('[data-testid="wizard-template-option-executive"]')` — tile exec
  - `page.locator('[data-testid="wizard-template-option-mass_hiring"]')` — mass hiring
  - `page.locator('[data-testid="wizard-template-option-intern"]')` — estágio
  - `page.locator('[data-suggested="true"]')` — qualquer tile sugerido (badge "Sugerido")
- Brief usava `[data-template-id="..."]` — atributo NÃO existe; o atributo real é `data-testid="wizard-template-option-..."`.

### Tile sugerido (badge "Sugerido")
- `WizardPipelineTemplateCard.tsx:100` — `data-suggested={isSuggested ? "true" : undefined}`.
- **Recomendado:** `[data-testid="wizard-template-option-${id}"][data-suggested="true"]`. Cobre os asserts de "tile X é o sugerido" sem text match.

### Card de candidato no chat (calibração)
- Vive dentro de `WizardCalibrationPanel.tsx:91-157` — **dead code**, ver acima. No `CalibrationPanel` real, não inspecionei testids.
- **Recomendado:** primeiro wirar o painel real, depois decidir.

### Card de candidato no kanban/funil
- `src/components/pages/job-kanban/KanbanColumnRenderer.tsx` tem `data-testid="candidate-card"` ✅.
- **Recomendado:** `page.locator('[data-testid="candidate-card"]')` quando navegando para a tela de funil/kanban da vaga.

### Chip contextual (PromptSuggestionsPanel)
- `src/components/PromptSuggestionsPanel.tsx:234-249` — botão `<button key={chip.prompt} ...>` no `flex flex-wrap gap-2`. **Sem `data-testid`.**
- O bloco só renderiza se `workflowContext` for passado e for diferente de `'idle'`. **Zero callers passam essa prop em `src/`** (ver Seção 2 abaixo).
- **Recomendado:** mesmo se wirado, `page.getByRole('button', { name: /Iniciar triagem|Calibrar busca|Entrevistadores|Compartilhar vaga/i })` cobre sem testid.

### TaskContextBar
- `src/components/unified-chat/wizard/TaskContextBar.tsx:121-177` — root `<div className="relative">`, sem `data-testid`. Texto `"📂 {currentAction}"` em `:126`. Botão "Switch Task" em `:131-143` (só visível quando `hasOtherTasks`).
- **Recomendado:** `page.getByText(/^📂/)` para o bar; `page.getByRole('button', { name: /Switch Task/i })` para o botão.

### WSI question card individual
- `WizardWSIListPanel.tsx:74-149` (dead code) — `QuestionRow` com `role="checkbox"` em `:96`. Sem testid.
- Se algum dia usado: `page.locator('[role="checkbox"]')` na lista WSI.
- O painel real (`WsiQuestionsPanel`) precisa inspeção separada.

### JD quality score badge
- `WizardJDReviewPanel.tsx:36-45` (dead code) — `<span>` com classes condicionais (verde / âmbar / vermelho), texto `"Ótimo · ${score}/100"` etc. Sem testid.
- **Recomendado:** `page.getByText(/\d+\/100/)` se ressuscitar o painel; ou parsear o WS frame que carrega `qualityScore`.

### Banner/chip de `missing_fields`
- **NÃO existe na UI.** `useWizardIntegration.ts:75,83-86` armazena `missingFields` em state mas **nenhum componente renderiza a lista** (grep por `missingFields` no JSX retorna zero). O state é exposto pelo hook mas nunca consumido.
- Cenário E precisará observar isso de outra forma — provavelmente interceptando o WS frame `wizard_step_response.missing_fields` via `page.waitForResponse` ou `page.on('websocket')`.

---

## Seção 2 — Gap entre brief original e UI atual

| Testid imaginado | Status | Ação | Cenários impactados |
|---|---|---|---|
| `unified-chat` | (c) ausente | usar `[data-testid="lia-bubble"]` ou `[data-testid="wizard-progress-bar"]` como âncora | A–G |
| `lia-message` | (b) fallback fuzzy | `.lia-markdown-content` (`UnifiedMessageList.tsx:327`) | A–G |
| `wizard-pipeline-template-card` | (a) existe como `wizard-template-card` | renomear no spec | A,B,C,D |
| `[data-template-id="..."]` | (a) existe como `[data-testid="wizard-template-option-${id}"]` | renomear no spec | A,B,C,D |
| `[data-suggested="true"]` | (a) existe ✅ | usar como está | A,B,C,D |
| `wizard-jd-review-panel` | **(c) painel é dead code** | **BLOCKER** — wirar `WizardJDReviewPanel` (ou usar `ReviewPanel` real) primeiro | A,B,C,D |
| `wizard-wsi-list-panel` | **(c) painel é dead code** | **BLOCKER** — wirar `WizardWSIListPanel` (ou usar `WsiQuestionsPanel` real) primeiro | A,B,C,D |
| `wizard-calibration-panel` | **(c) painel é dead code** | **BLOCKER** — wirar `WizardCalibrationPanel` (ou usar `CalibrationPanel` real) primeiro | F |
| `wsi-question-card` | (c) ausente; no painel real precisa inspeção | depende de qual WSI panel for wirado | A,B,C,D |
| `jd-quality-score` | (c) ausente — nem texto separado tem | ler do WS frame ou pular assert | A,B |
| `missing-fields-warning` | **(c) ausente — `missingFields` setado mas nunca renderizado** | **BLOCKER de UX** — não há banner; cenário E vira "interceptar WS frame" | E |
| `wizard-current-stage` | (b) `[data-testid="wizard-progress-bar"]` mostra o widget mas não expõe stage diretamente | usar progress-bar para visibilidade; stage exato via WS | A–E |
| `contextual-chip` | **(c) `workflowContext` nunca é passado** | **BLOCKER** — chips definidos mas não renderizados na UI | F,G |
| `candidate-card` (chat) | (c) ausente (painel calibration é dead code) | depende de wiring | F |
| `candidate-card` (kanban) | (a) existe em `KanbanColumnRenderer.tsx` ✅ | usar como está, navegando para o kanban da vaga | G |
| `must-have-criteria-table` | (c) tabela renderizada apenas em `WizardCalibrationPanel` (dead code) | depende de wiring | F |
| placeholder `"Faça qualquer coisa com a LIA..."` | (c) string não existe no source — placeholder vem de `t('placeholder')` (i18n) | usar `getByRole('textbox')` | A–G |
| botão "Aceitar" / "Aceitar selecionadas" / "Finalizar calibração" | (b) existem em painéis dead code com aria-label fixo | depende de wiring | A,B,C,D,F |

### Detalhamento dos 4 BLOCKERS

#### BLOCKER 1 — 3 painéis Wizard são dead code

`WizardJDReviewPanel`, `WizardWSIListPanel`, `WizardCalibrationPanel` existem em `src/components/unified-chat/wizard/panels/` mas:
- **Zero callers** em todo `src/` (`rg -l 'WizardJDReviewPanel|WizardWSIListPanel|WizardCalibrationPanel'` retorna apenas os próprios arquivos).
- **Não exportados** de `src/components/unified-chat/wizard/index.ts` (que exporta `DynamicContextPanel`, `TaskContextBar`, `WizardProgressBar`, etc., mas não os 3 painéis).
- O renderizador real (`DynamicContextPanel.tsx:11-47`) importa **outros** componentes: `ReviewPanel`, `WsiQuestionsPanel`, `CalibrationPanel` (sem prefixo `Wizard`).

**Hipótese:** os 3 `Wizard*` foram refactor/redesign que ficou fora do wiring final (Onda 26-27 E.2/E.3/E.4 entregou os arquivos mas a integração com `DynamicContextPanel` nunca aconteceu).

**Impacto:** assertions tipo `expect(page.locator('[data-testid="wizard-jd-review-panel"]')).toBeVisible()` vão sempre falhar não por bug de selector, mas porque o componente não está em tela. Cenários A,B,C,D,F não são cobríveis nesta forma.

**Caminhos possíveis (decisão de produto, não de QA):**
1. Wirar os 3 painéis novos no `DynamicContextPanel` (substituir os antigos), aí escrever specs.
2. Adaptar os specs para usar os painéis reais (`ReviewPanel`, `WsiQuestionsPanel`, `CalibrationPanel`) — mas eles têm UI diferente e provavelmente não cobrem os asserts do brief.
3. Excluir os 3 `Wizard*` se forem refugo (canonical-fix).

**Recomendação de QA:** abrir issue de produto antes da Fase 2, decidir 1/2/3, daí escrever specs.

#### BLOCKER 2 — `workflowContext` chips nunca renderizados

`PromptSuggestionsPanel.tsx:78-80,216-253` define a prop `workflowContext` e os chips contextuais (`vacancy_published`: "Iniciar triagem", "Calibrar busca", etc.).

`rg -n 'workflowContext' src/` retorna **apenas o próprio arquivo** — nenhum caller em `src/components/unified-chat/` ou outro lugar passa essa prop. Os chips contextuais nunca aparecem na UI, em nenhum estado.

**Impacto:** Cenário F (clicar em chip pós-publicação) e Cenário G (clicar "Iniciar triagem" para disparar busca) são **inalcançáveis** pelo fluxo de UI. Não há entry point.

**Caminho:** wirar `PromptSuggestionsPanel` no `UnifiedChat` quando `WorkflowContext === 'vacancy_published'` (após `wizard_stage = 'done'`/`'handoff'`). Sem isso, F e G ficam descobertos.

#### BLOCKER 3 — `missing_fields` capturado mas nunca exibido

`useWizardIntegration.ts:75,83-86` extrai `stepResponse.missing_fields` do WS frame e armazena em state (`setMissingFields`). Mas **nenhum componente lê esse state** — `rg -n 'missingFields' src/components/` retorna apenas o próprio hook (escrita, sem leitura).

**Impacto:** Cenário E (validators bloqueiam avanço, "⚠️ Campos obrigatórios em aberto") não tem banner em tela. O backend manda, o frontend recebe, mas não mostra.

**Caminho:**
1. Wirar um `MissingFieldsBanner` no `UnifiedChat` que consuma `missingFields` do hook. OU
2. Cenário E vira "interceptar o WS frame `wizard_step_response.missing_fields` via `page.on('websocket')`" — sensor estrutural, não visual.

#### BLOCKER 4 — Cenário G entry point depende do BLOCKER 2

Mesmo se o BLOCKER 2 for resolvido, "clicar chip Iniciar triagem → dispara busca → candidatos no kanban" requer:
- Frontend: chip wirado (BLOCKER 2). ✅ resolvido por BLOCKER 2.
- Backend: endpoint de busca refinada existir e popular o kanban. **Não inspecionado nesta auditoria** — abrir issue separada para validar.
- Frontend: `[data-testid="candidate-pool-result"]` que o brief assume — não verifiquei se existe.

---

## Seção 3 — Reuso de fixtures e specs existentes

### `e2e/fixtures/wizard-conversation.fixture.ts` (124 linhas)

Inspecionado linha a linha. Funções:

| Helper | O que faz | Reuso recomendado |
|---|---|---|
| `sendWizardMessage(page, text, waitForResponse)` | Localiza textarea fuzzy, fill, clica send/Enter, aguarda `[data-testid="lia-thinking"]` ou fallback `waitForTimeout(2000)` | **Estender** — substituir o `waitForTimeout(2000)` por `page.waitForResponse(/ws\/chat|api\/v1\/chat/)` e remover o `lia-thinking` (não verifiquei se existe). |
| `fillWizardStep(page, messages[])` | Loop de `sendWizardMessage` | **Reusar integralmente** |
| `assertWizardProgress(page, expectedStage)` | Tenta vários selectors `[data-stage="..."]`/`[data-testid="wizard-stage-..."]`/`.wizard-stage.active`, todos provavelmente inexistentes; faz `console.log` se não achar | **Reescrever** — usar `[data-testid="wizard-progress-bar"]` para visibilidade + interceptar WS frame `wizard_stage` para o stage exato. |
| `waitForJobPublished(page)` | Race entre `waitForURL('**/vagas/**')` e text match `:has-text("publicada"\|"criada com sucesso")` | **Reusar integralmente** — bom padrão. |
| `openJobWizard(page)` | `page.goto('/vagas/nova')` + `networkidle` + aguarda chat ready | **Reusar integralmente** se a rota `/vagas/nova` existir; senão adaptar para o entry point real (provavelmente abrir bubble + digitar "criar vaga"). |

**Funções novas a adicionar (na própria `wizard-conversation.fixture.ts`, mantendo escopo):**
- `expectLiaLastMessageMatches(page, regex)` — pega `.lia-markdown-content` last e faz `expect(...).toContainText(regex)`.
- `waitForWizardStepResponse(page)` — `page.waitForResponse` com filtro pelo URL do WS de chat, capturando `wizard_step_response.metadata`.
- `pickPipelineTemplate(page, type: 'technical'|'executive'|'operational'|'mass_hiring'|'intern')` — clica `[data-testid="wizard-template-option-${type}"]`.

### `e2e/tests/job-creation/*.spec.ts` (6 specs, 1500 linhas total)

| Spec | Cobre hoje | Sobreposição com A-G | Recomendação |
|---|---|---|---|
| `01-create-modal.spec.ts` | Modal manual: validação de campos, submit mínimo/completo, voltar reseta form | **Zero** — modal-driven, fluxo paralelo ao chat-driven | Deixar como está |
| `02-edit-basic-info.spec.ts` | Editar título, departamento, modelo, faixa salarial, status pelo modal de edição | **Zero** — pós-criação, edição estrutural | Deixar como está |
| `03-edit-requirements.spec.ts` | JobEditTab: Settings, requisitos, benefícios, etapas | **Zero** — edição de vaga existente | Deixar como está |
| `04-screening-config.spec.ts` | ScreeningConfigManager: ativar triagem, canais, perguntas custom, min_score | Cobre **parcialmente** o conteúdo WSI mas pelo modal de Settings, não pelo chat | Deixar como está; novos specs do wizard são fluxo separado |
| `05-job-publishing.spec.ts` | Modal de publicação: LinkedIn, Portal Carreiras, despublicar/congelar | Cobre **parcialmente** o "stage publication" do brief mas via modal | Deixar como está |
| `06-complete-flow.spec.ts` | Fluxo completo modal: criar → editar → triagem → publicar; edge cases (chars, duplicado) | Cobre o **outcome** dos cenários A-D (vaga publicada) por outro caminho | Deixar como está; novos specs do wizard testam o **caminho conversacional** |

**Conclusão:** os 6 specs `job-creation/` testam o fluxo **modal-driven** (criar vaga clicando em formulário). Os cenários A-G do brief testam o fluxo **chat-driven** (criar vaga conversando com a LIA). Não há conflito nem grande sobreposição. Os novos specs em `e2e/tests/wizard/` ficam separados.

`e2e/fixtures/job-creation.fixture.ts` (não inspecionei em detalhe) exporta `SEL`, `uniqueJobTitle`, `TEST_JOB_MINIMAL`, `TEST_JOB_FULL` — pode ser reusado em cenários do wizard que precisem gerar título único ou validar a vaga criada (via `SEL` apontando para listagem de vagas).

---

## Seção 4 — Data-testids recomendados como Boy Scout

### Recomendação: **0 testids nesta fase.**

Justificativa:
1. **Os elementos onde testids fariam diferença (`WizardJDReviewPanel`, `WizardWSIListPanel`, `WizardCalibrationPanel`) são dead code.** Adicionar testid em código que não está renderizado é puro desperdício — o teste continua falhando porque o elemento não está em tela.
2. **`PromptSuggestionsPanel` (chips contextuais) não é renderizado** porque ninguém passa `workflowContext`. Adicionar testid no botão não resolve — o `if (showContextChips)` não vira true.
3. **`missing_fields` não tem renderização** — não existe componente para receber testid.
4. **`WizardPipelineTemplateCard`** já tem testids (`wizard-template-card`, `wizard-template-option-${id}`, `data-suggested`) — sem necessidade de mais.
5. Pra todo elemento estável que falta (`textarea`, `lia-message bubble`, `TaskContextBar`), há fallback acessível razoável (`getByRole`, `.lia-markdown-content`, `aria-label`). Não vale o ruído de produção.

### Quando faria sentido adicionar testid (após resolver os BLOCKERS)

Se a decisão de produto for **wirar os 3 painéis novos**, então sim, esses 3 (no máximo) seriam justificáveis:

```
1. data-testid="wizard-jd-review-panel"
   Onde: WizardJDReviewPanel.tsx:118, no <div className="flex flex-col h-full"> raiz
   Justificativa: 4 cenários (A,B,C,D) precisam saber quando o painel HITL gate 1 abre
   Custo: 1 linha, zero risco
   Pré-requisito: BLOCKER 1 resolvido

2. data-testid="wizard-wsi-list-panel"
   Onde: WizardWSIListPanel.tsx:208
   Justificativa: idem para HITL gate 2; conta de questões precisa saber se está no painel certo
   Pré-requisito: BLOCKER 1 resolvido

3. data-testid="wizard-calibration-panel"
   Onde: WizardCalibrationPanel.tsx:180
   Justificativa: Cenário F precisa do painel; toggle "Open criteria" precisa âncora
   Pré-requisito: BLOCKER 1 resolvido
```

`PromptSuggestionsPanel` não precisa de testid mesmo após wiring — `getByRole('button', { name: /Iniciar triagem/i })` resolve sem produção.

`MissingFieldsBanner` não existe — se for criado, viria com testid próprio na PR de criação (não Boy Scout).

---

## Boy Scout — fixes oportunísticos sugeridos (não aplicar)

Encontrados durante audit. **Não corrigi nada** (modo read-only).

1. **`WizardJDReviewPanel` / `WizardWSIListPanel` / `WizardCalibrationPanel` são dead code.** Decidir entre wirar ou deletar (canonical-fix). Hoje são ~740 linhas de código sem caller, sem teste unitário, sem story. Risco: drift entre o que se acredita estar em tela e o que está.
2. **`useWizardIntegration.ts:75,83-86`** seta `missingFields` mas **nunca expõe nem é lido por nenhum componente** que renderize. Ou wirar um banner, ou remover o state morto.
3. **`PromptSuggestionsPanel.workflowContext`** prop órfã — nenhum caller. Ou wirar no `UnifiedChat`, ou remover o branch `if (showContextChips)` (~30 linhas).
4. **`fixtures/wizard-conversation.fixture.ts:48`** usa `page.waitForTimeout(2000)` como fallback explícito — viola "no flaky tests". Substituir por `waitForResponse` filtrado pelo URL do WS de chat.
5. **`fixtures/wizard-conversation.fixture.ts:42`** procura `[data-testid="lia-thinking"]` que provavelmente não existe (não achei no grep amplo da Seção 1). Ou criar o testid no componente que renderiza o estado "thinking", ou remover o branch.
6. **`assertWizardProgress`** (linhas 72-94) tem 3 selectors em fallback, todos provavelmente quebrados, e termina com `console.log` em vez de assert. Função vira no-op silencioso. Ou implementar de verdade ou remover.

---

## Disciplinas — classificação de gaps

| Gap | Tipo (sensor / guide) | Severidade |
|---|---|---|
| 3 painéis Wizard dead code (BLOCKER 1) | sensor estrutural ausente | P0 — bloqueia 5 cenários |
| `workflowContext` nunca passado (BLOCKER 2) | sensor estrutural ausente | P0 — bloqueia 2 cenários |
| `missing_fields` sem renderização (BLOCKER 3) | sensor estrutural ausente | P1 — cenário E vira sensor de WS, não visual |
| Cenário G entry point indireto (BLOCKER 4) | sensor — depende de BLOCKER 2 | P1 |
| Selectors brief vs reais (Seção 2 não-blocker) | renomeação trivial | P2 — fix no spec quando for escrever |
| `[data-testid="unified-chat"]` ausente | sensor — fallback fácil via `lia-bubble` ou `wizard-progress-bar` | P2 |
| `[data-testid="lia-message"]` ausente | sensor — fallback `.lia-markdown-content` | P2 |
| `placeholder` literal não existe | guide (texto i18n) — usar `getByRole` | P2 |
| `assertWizardProgress` no-op silencioso | guide — função existe mas não testa nada | P2 (Boy Scout #6) |

---

## Próximos passos sugeridos (decisão tua)

**Antes da Fase 2 (escrever specs), decidir:**

1. **BLOCKERS 1+2+3** — wirar os 3 painéis + chips + banner, OU adaptar os 7 cenários para usar os componentes reais (`ReviewPanel`/`WsiQuestionsPanel`/`CalibrationPanel`) e remover asserts dos chips/banner.
2. **Cenário G** — verificar se o endpoint de "busca refinada → popular kanban" existe no backend (não auditei). Se não existe, G fica como issue de produto separada.

**Após decisão:**

- Se opção "wirar primeiro": abrir 3 PRs (wirar 3 painéis, wirar chips, wirar banner) → mergear → daí escrever specs com os 5 testids justificáveis.
- Se opção "adaptar specs": reescrever Cenários A-D com seletores dos painéis reais (precisa nova rodada de audit nesses arquivos), excluir asserts dos chips em F, transformar E em sensor de WS.

---

**Tamanho:** ~365 linhas (limite ≤400). Sem código de produção tocado. Working tree dirty: apenas `plataforma-lia/e2e/reports/wizard-e2e-AUDIT.md`.
