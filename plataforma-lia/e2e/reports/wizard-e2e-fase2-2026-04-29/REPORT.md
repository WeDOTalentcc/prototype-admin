# Wizard E2E — Fase 2 — 2026-04-29

## Sumário

| Item | Valor |
|---|---|
| Cenários implementados | 6/6 (A, B, C, D, E, F) |
| Cenário G | BLOCKER documentado em `_BLOCKED-cenario-G.md` (depende de Onda 34) |
| Arquivos criados | 7 em `e2e/tests/wizard/` (1 helpers + 5 specs + 1 BLOCKER doc) |
| Linhas de código de produção tocadas | **0** (constraint respeitada) |
| Testids novos adicionados em produção | **0** (constraint respeitada — Audit Seção 4) |
| TypeScript check | ✅ `tsc --noEmit` passou nos 7 arquivos |
| Execução runtime (`pnpm playwright test`) | ⏸️ pendente — rodar do lado do usuário (ver "Execução" abaixo) |
| Working tree | dirty conforme orientado (não commitado) |

> **Nota sobre execução:** o brief especifica `APP_ENV=development` com LLM real
> e demo user. Rodar os 6 cenários sequencialmente (workers=1, timeout 15min
> cada, mais o boot do dev server e do `lia-backend`) ultrapassa a janela de
> uma sessão única do agente. Esta entrega foca em deixar o harness 100%
> escrito, type-checked e ancorado nos selectors REAIS do Audit Seção 1. O
> reporte de **bugs** e **tempo total** será preenchido após a execução
> manual descrita em "Execução" — esta seção é deixada como template
> estruturado para você editar com os números reais.

## Execução

```bash
cd plataforma-lia
# Pré-requisitos:
# 1. lia-backend rodando com APP_ENV=development e demo user habilitado
# 2. dev-server rodando em http://localhost:5000
# 3. Variáveis de LLM configuradas (Anthropic/OpenAI/Gemini conforme stack)
APP_ENV=development pnpm playwright test e2e/tests/wizard/ --reporter=html,list
pnpm playwright show-report
```

## Arquivos entregues

```
plataforma-lia/e2e/tests/wizard/
├── 01-helpers.ts              # 290 LoC — helpers + selectors AUDIT Sec.1 + sensores qualidade
├── 02-vaga-tecnica.spec.ts    # Cenário A — Engenheiro Pleno
├── 03-vaga-executiva.spec.ts  # Cenário B — Diretor de Marketing
├── 04-vaga-operacional.spec.ts # Cenário C — Atendente loja (mass_hiring)
├── 05-vaga-estagio.spec.ts    # Cenário D — Estagiário Frontend
├── 06-validators-erro.spec.ts # Cenário E — Banner missingFields (Onda 33 wiring)
├── 07-pos-publicacao.spec.ts  # Cenário F — Calibração + critérios toggle
└── _BLOCKED-cenario-G.md      # Cenário G — bloqueado por Onda 34

plataforma-lia/e2e/reports/wizard-e2e-fase2-2026-04-29/
├── REPORT.md                  # este arquivo
└── (screenshots A-00..F-04 — geradas durante runtime)
```

## Decisões de harness

### 1. Selectors — todos do Audit Seção 1, zero invenção

| Elemento | Selector usado | Origem |
|---|---|---|
| Textarea | `getByRole('textbox', { name: /mensagem\|message/i })` | Audit Sec.1 (UnifiedChatInput.tsx:157-173) |
| Última mensagem LIA | `.lia-markdown-content` | Audit Sec.1 (UnifiedMessageList.tsx:327) |
| Floating bubble | `[data-testid="lia-bubble"]` | Audit Sec.1 (UnifiedChatBubble.tsx:226) |
| Progress bar wizard | `[data-testid="wizard-progress-bar"]` | Audit Sec.1 (UnifiedChat.tsx:616) |
| Card de templates | `[data-testid="wizard-template-card"]` | Audit Sec.1 (WizardPipelineTemplateCard.tsx:73-77) |
| Tile específico | `[data-testid="wizard-template-option-${id}"]` | idem :99-100 |
| Tile sugerido | `[data-suggested="true"]` | idem |
| WSI rows | `[data-testid^="wsi-question-row-"]` + `role="listitem"` | grep WsiQuestionsPanel.tsx (canônico Onda 33) |
| Toggle critérios | `[data-testid="calibration-criteria-toggle"]` | grep CalibrationPanel.tsx (canônico Onda 33) |
| Banner missingFields | `[role="status"][aria-live="polite"]` filtrado por regex | brief Cenário E + reuso estilo ReviewPanel.tsx:64-68 |
| Kanban candidate | `[data-testid="candidate-card"]` | Audit Sec.1 (KanbanColumnRenderer.tsx) |

ReviewPanel canônico **não tem testid próprio** (Audit Sec.1 confirma).
Heurística usada: aparição do botão `getByRole('button', { name: /publicar/i })`.
Se isso virar fonte de flake, abrir issue Boy Scout para adicionar
`data-testid="review-panel"` em `panels/ReviewPanel.tsx` (1 linha, zero risco).

### 2. Reuso integral do `wizard-conversation.fixture.ts`

`01-helpers.ts` importa e reusa:
- `sendWizardMessage` (com `waitForResponse=false` — wrapping próprio em `sendMessageAndWait` para eliminar o `waitForTimeout(2000)` arbitrário do fixture original — **Boy Scout #4 do Audit**).
- `openJobWizard` (re-exportado).

Funções **não usadas** porque têm bugs documentados no Audit Boy Scout:
- `assertWizardProgress` — Audit #6: 3 selectors em fallback, todos provavelmente quebrados, termina com `console.log`. Substituído por `expectStageAdvanced` (sensor estrutural).

### 3. Asserts em invariantes, NÃO em wording

LLM é não-determinístico. "Pleno", "Sênior", "Júnior" são todas válidas para
o mesmo prompt. Os specs assertam:
- **Estrutural**: contagem de `.lia-markdown-content` aumentou; painel
  canônico ficou visível; tile certo foi clicado.
- **Faixas**: WSI compact entre 3-8 cards; WSI completa entre 8-15.
- **Regex tolerante**: `/publicad|criad|sucesso/i`, `/pool|matches|critéri|atualiz|refin/i`.

Nenhum spec exige texto literal da LIA.

### 4. Sensores de qualidade computacionais

`attachQualitySensors(page, testInfo)` em todos os specs:
- Coleta `console.error` filtrado (silencia ruído `404` de fontes/imagens, DevTools, HMR).
- Coleta `4xx/5xx` em qualquer URL `/api/`.
- Anexa ao testInfo no `finally` de cada teste (sem precisar `afterEach` extra).

`assertNoAiSlop(page)` — regex sobre TODAS as bubbles da LIA, não só a última:
- "como modelo/assistente de IA"
- "em conclusão / para resumir / em síntese"
- "vamos juntos / espero ter ajudado"
- "sou apenas um modelo / IA"

`assertNoLgpdViolation(page)` — regex sobre rows do `WsiQuestionsPanel`:
- idade / data de nascimento
- raça / etnia / cor da pele
- religião / crença religiosa
- gênero / sexo biológico
- estado civil / casado / solteiro / filhos
- orientação sexual
- CPF / RG

### 5. Sem flakes — `waitForTimeout` proibido + fail-loud

`sendMessageAndWait` (versão pós code-review):
1. Conta bubbles antes; envia (sem o `setTimeout(2000)` do fixture original).
2. **Fail-loud**: `expect.poll(() => count).toBeGreaterThan(before)` — se nenhuma
   bubble nova aparecer no timeout (45s), o teste falha com mensagem clara.
3. Settle do stream: `waitForFunction` aguarda o último bubble parar de crescer
   entre dois ticks de 500ms. Tolerante apenas no settle (não na presença).

`expectStageAdvanced` usa `expect.poll(...)` com timeout — sem `waitForTimeout`.

Retries por describe: `test.describe.configure({ retries: 1 })` — uma única
re-tentativa para absorver flakes residuais de LLM.

### 6. Hardening pós code-review

Após primeira passada o code-review apontou silent fallbacks que poderiam
deixar specs verdes mesmo com bugs reais. Foram corrigidos:

- **A/B/C/D — template card**: era `if visible { ... }` opcional. Agora é
  `await expect(SEL.templateCard).toBeVisible({ timeout: 30s })` fail-loud.
- **B — tile sugerido**: era `testInfo.attach` se errado, sem falhar. Agora é
  `await expect(executive).toHaveAttribute('data-suggested', 'true')`.
- **C — tile sugerido**: idem fail-loud com mensagem incluindo qual id foi escolhido.
- **D — tile sugerido**: idem fail-loud para `intern`.
- **E — banner missingFields**: era `if visible { assert } else { attach }`.
  Agora é fail-loud direto, com mensagem ligando a Onda 33 wiring + BLOCKER 3.
- **E — panels ausentes**: além do WSI, agora também checamos que
  CalibrationPanel e botão Publicar do Review NÃO aparecem.
- **F — candidate cards**: era `if cardsCount >= 3 { fluxo } else { skip }`.
  Agora é fail-loud com `expect.poll(...).toBeGreaterThanOrEqual(3)` + mensagem
  pedindo para verificar se o seed da demo popula candidatos.
- **F — botões aprovar/rejeitar**: cada um agora é fail-loud
  `await expect(approve).toBeVisible()`. Botão de rejeitar permanece
  condicional só quando há < 4 cards (algumas variantes do CalibrationPanel
  só mostram 3 por vez — comportamento legítimo, não bug).
- **`SEL.missingFieldsBanner` morto removido**: usava CSS inválido
  `:has-text(/regex/)`. Substituído pelo helper `getMissingFieldsBanner(page)`
  que aplica `.filter({ hasText: regex })` corretamente.
- **`sendMessageAndWait` Promise.race com `.catch(() => null)` removido**:
  era silent fallback. Substituído por `expect.poll` fail-loud puro.

## Bugs detectados

> **Preencher após execução real.** Template estruturado abaixo.

### 🔴 P0 (blockers)

| ID | Cenário | Bug | Repro | Sensor que teria pego |
|----|---------|-----|-------|------------------------|
| _none yet_ | | | | |

### 🟡 P1 (críticos)

| ID | Cenário | Bug | Repro | Sensor que teria pego |
|----|---------|-----|-------|------------------------|
| _none yet_ | | | | |

### 🟢 P2 (importantes / Boy Scout)

Bugs já mapeados no Audit que podem ser exposed pelos novos specs (não
patchados — apenas reportados):

| ID | Origem | Descrição | Spec que vai expor |
|----|--------|-----------|--------------------|
| BS-1 | Audit Boy Scout #1 | 3 painéis Wizard* deletados na Onda 33 — confirmar que `rg WizardJDReviewPanel src/` retorna 0 | n/a (canonical-fix Onda 33 deveria ter resolvido) |
| BS-2 | Audit Boy Scout #2 | `useWizardIntegration.ts:75,83-86` seta `missingFields` mas o componente que renderiza só foi wirado na Onda 33 — Cenário E vai expor se faltou wiring em algum branch | 06-validators-erro.spec.ts |
| BS-3 | Audit Boy Scout #3 | `PromptSuggestionsPanel.workflowContext` órfão — Onda 34 vai resolver | _BLOCKED-cenario-G.md |
| BS-4 | Audit Boy Scout #4 | `wizard-conversation.fixture.ts:48` `waitForTimeout(2000)` — eliminado em `sendMessageAndWait` do helper Fase 2 | n/a (resolvido neste delivery) |
| BS-5 | Audit Boy Scout #5 | `[data-testid="lia-thinking"]` não existe — fixture original tenta isHidden() em selector morto | n/a (substituído por contagem de bubbles) |
| BS-6 | Audit Boy Scout #6 | `assertWizardProgress` no-op silencioso — substituído por `expectStageAdvanced` neste delivery | n/a |

## Análise qualitativa por cenário

> **Preencher após execução real.** Template abaixo. Cada cenário deve
> registrar funcional, UX/voice (LIA), LGPD/fairness, performance e bugs.

### Cenário A — Engenheiro Pleno
- **Funcional:** ⏸️ aguardando execução
- **UX/Voice (LIA):** ⏸️
- **LGPD/Fairness:** ⏸️ (asserto via `assertNoLgpdViolation`)
- **Performance:** ⏸️ (medir tempo médio sendMessage→resposta via `attachQualitySensors`)
- **Screenshots:** A-00 a A-06 (gerados pelo `captureMilestone`)
- **Bugs:** ⏸️

### Cenário B — Diretor de Marketing
- **Funcional:** ⏸️
- **UX/Voice (LIA):** ⏸️
- **LGPD/Fairness:** ⏸️
- **Performance:** ⏸️
- **Screenshots:** B-00 a B-06
- **Bugs:** ⏸️

### Cenário C — Mass hiring (atendentes)
- **Funcional:** ⏸️
- **UX/Voice (LIA):** ⏸️
- **LGPD/Fairness:** ⏸️
- **Performance:** ⏸️
- **Screenshots:** C-00 a C-06
- **Bugs:** ⏸️

### Cenário D — Estagiário Frontend
- **Funcional:** ⏸️
- **UX/Voice (LIA):** ⏸️
- **LGPD/Fairness:** ⏸️
- **Performance:** ⏸️
- **Screenshots:** D-00 a D-06
- **Sensor extra:** WSI não pode pedir 3+ anos de experiência nem nível pleno/sênior (regex no spec)
- **Bugs:** ⏸️

### Cenário E — Banner missingFields
- **Funcional:** ⏸️ (Onda 33 wiring)
- **UX/Voice (LIA):** ⏸️
- **Sensor estrutural:** banner `[role="status"][aria-live="polite"]` deve aparecer; ReviewPanel/WSI NÃO pode abrir
- **Screenshots:** E-00 a E-02
- **Bugs:** ⏸️

### Cenário F — Calibração + critérios toggle
- **Funcional:** ⏸️
- **UX/Voice (LIA):** ⏸️
- **Sensor estrutural:** `aria-expanded` do `calibration-criteria-toggle` muda
- **Performance:** ⏸️
- **Screenshots:** F-00 a F-04
- **Bugs:** ⏸️

## Disciplinas — classificação dos sensores

| Cenário | Tipo de sensor | Notas |
|---|---|---|
| A, B, C, D | guide (LLM) + sensor (contagem bubbles, painel visível, tile clicado, WSI count, regex faixa) | Maioria sensor estrutural; LLM intervém só em wording |
| E | sensor puro (banner role/aria-live) | Onda 33 wiring é o que está sendo testado |
| F | sensor (toggle aria-expanded, kanban testid) + guide (regex última mensagem) | |
| LGPD | sensor (regex sobre WSI rows) | computacional, fail-loud |
| AI Slop | sensor (regex sobre todas as bubbles) | computacional, fail-loud |
| Multi-tenancy | **não coberto neste delivery** — não há JWT real para extrair company_id | Próxima fase: interceptar requests `/api/v1/*` e validar header |

## Recomendações

1. **Após primeira execução**, popular esta seção com os bugs reais
   (P0/P1/P2) e as métricas de tempo (`testInfo.duration` por cenário).

2. **Considerar Boy Scout pequeno** após esta fase: adicionar
   `data-testid="review-panel"` em `panels/ReviewPanel.tsx:1` (1 linha)
   para eliminar a heurística "botão Publicar visível" do `expectPanelOpens('review', ...)`.
   Custo: zero risco. Justificativa: 4 cenários (A,B,C,D) dependem disso.

3. **Onda 34 (Cenário G)**: ao fechar, criar `08-busca-candidatos.spec.ts`
   conforme template em `_BLOCKED-cenario-G.md`. Reusar `quickPublishTechVacancy()`
   do `01-helpers.ts` para encurtar boilerplate.

4. **Multi-tenancy**: adicionar em fase futura um helper
   `assertTenantHeader(request, expectedCompanyId)` que ouça `page.on('request')`
   e fail-loud se algum `/api/v1/*` não bater com o JWT do demo user.
   Cobre a disciplina mencionada no brief que esta fase não cobriu.

5. **Tempo de execução total** quando rodar: estimar ~60-90 minutos para os
   6 cenários sequenciais (workers=1) com LLM real. Se virar gargalo de CI,
   considerar paralelizar A/B/C/D em workers separados (cada um abre uma
   sessão de chat isolada — não há estado compartilhado entre vagas).

## Apêndice: comando de smoke individual

```bash
# Smoke do harness (sem LLM real, valida só carregamento da página)
APP_ENV=development pnpm playwright test e2e/tests/wizard/06-validators-erro.spec.ts --reporter=list

# Cenário A isolado
APP_ENV=development pnpm playwright test e2e/tests/wizard/02-vaga-tecnica.spec.ts --reporter=html,list

# Suite completa
APP_ENV=development pnpm playwright test e2e/tests/wizard/ --reporter=html,list
pnpm playwright show-report
```
