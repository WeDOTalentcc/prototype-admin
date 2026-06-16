# Cenário G — BLOCKER condicional (Onda 34 pendente)

**Status:** não implementado nesta Fase 2.

**Razão:** Cenário G ("busca de candidatos pós-calibração via chip Iniciar
triagem") depende de `PromptSuggestionsPanel` + `workflowContext === "vacancy_published"`.
Audit `wizard-e2e-AUDIT.md` (Seção 2 — BLOCKER 2 e 4) confirmou que esse
painel é dead code (zero callers em `src/`), e Onda 34 vai wirar.

Adicionalmente, BLOCKER 4 do mesmo Audit registra que mesmo após o wiring
do chip, o endpoint backend de "busca refinada → popular kanban" precisa
ser validado separadamente (não auditado nesta fase).

**Após Onda 34 fechar:** adicionar `08-busca-candidatos.spec.ts` cobrindo:

1. Pré-condição: vaga já publicada (reusar `quickPublishTechVacancy()` de `01-helpers.ts`)
2. Localizar chip `getByRole('button', { name: /Iniciar triagem/i })` e clicar
3. LIA dispara busca via WS — interceptar `page.waitForResponse(/\/api\/v1\/(sourcing|search|candidates)/i)`
4. Aguardar pool refinado aparecer (sensor estrutural — bubble da LIA com texto /pool|encontr|matches/i)
5. Navegar para `/vagas/${id}` → tab Funil/Kanban
6. Stage "Triagem" tem `[data-testid="candidate-card"]` em count >= 1
7. Cada card tem nome, score (regex /\d+%?/), botões de ação visíveis
8. `assertNoAiSlop()` + `attachQualitySensors()`

**Helpers extras a adicionar (em `01-helpers.ts`):**
- `expectChipVisible(page, name)` — fail-loud se chip não estiver renderizado
- `navigateToJobKanban(page, jobId)` — abre `/vagas/${jobId}` e clica tab Funil
- `extractCandidateCard(card)` — extrai `{ name, score }` de um candidate-card

**Dependência adicional:** confirmar com produto que o backend de
"busca refinada" popula `triagem` stage do kanban automaticamente, ou se
requer ação manual (drag, botão "Mover para triagem").
