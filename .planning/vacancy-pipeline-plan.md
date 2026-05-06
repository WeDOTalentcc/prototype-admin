# Plano canônico — Preview de vagas + ações por estágio + import direto ATS + wizard chat awareness

**Branch ativa (Replit):** `feat/benefits-prv-canonical`
**Owner:** Paulo (founder)
**Data:** 2026-05-06
**Status:** approved — em execução

> Este arquivo é a fonte canônica de verdade para o trabalho. Todos os agentes que rodarem SSH ao Replit devem ler este plano antes de tocar em qualquer arquivo do escopo.

---

## 1. Context — por que esse trabalho

A tela "Recrutar → Visão Global → Vagas" mostra 8 estágios de lifecycle (`ats_importada → rascunho → enriquecida → wsi_config → aguardando_aprovacao → publicada → ao_vivo → encerrada`). Backend está saudável (38/38 tests passam, classifier correto). Bulk import via CSV/JSON funciona. Mas a UX pós-importação é frágil:

1. Clicar num card de vaga abre o **kanban de candidatos** — errado pra vagas em `ats_importada/rascunho/enriquecida` que ainda não têm candidatos.
2. **Não há ações contextuais** por estágio na rail (revisar JD, gerar perguntas WSI, ativar dispatch, publicar, mudar status).
3. **BulkImportModal** só aceita CSV/JSON manual, não tem opção de importar direto do ATS conectado (Gupy/Pandapé) — embora **infraestrutura backend já esteja 100% pronta**.
4. O **wizard chat** (LIA) não detecta automaticamente o estágio da vaga e não oferece a próxima ação.
5. **`ReadinessHubPage`** (556 linhas) está órfão no codebase, gera confusão.

**Outcome esperado.** Recrutador vê todas as vagas progredirem visualmente; cada card tem CTA contextual que (a) abre preview lateral, (b) deep-linka pra section certa de `JobKanbanPage` tab `edit` (Configurações), ou (c) dispara ação direta (status change/publish). Pelo chat, LIA detecta estágio e oferece a próxima ação automaticamente.

---

## 2. Decisões de produto (Paulo dictou)

- **Faseamento:** ship cada fase quando estiver pronta; validação UI entre fases.
- **WSI questions:** sempre oferece compacta E completa. Ambas levam à tab `edit?section=perguntas` da vaga onde recrutador completa manualmente. Pelo chat = processo completo automatizado.
- **ReadinessHubPage:** deletar (refactor canonical, Phase 0).
- **CTAs PRÉ-triagem** (`ats_importada/rascunho/enriquecida/wsi_config/aguardando_aprovacao`) sempre vão pra `tab=edit`, NUNCA pro kanban.
- **CTAs PÓS-triagem** (`publicada/ao_vivo`) reusam modais existentes inline na rail.
- **Tudo deve estar disponível também via chat com LIA** — wizard tools 1-pra-1 com botões do preview.

---

## 3. Auditoria exaustiva (achados que mudam o plano)

### 3.1 ✅ Reutilização (já existe — economiza muito código)

| Coisa | Onde | Efeito no plano |
|---|---|---|
| `ScreeningConfigManager` com 3 sections (`configuracoes` / `descricao` / `perguntas`) | `plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx` | Phase B virou só deep-link via URL params |
| Prop `_externalActiveSection` que sobrescreve via `\|\|` | `useScreeningConfigManagerCore.ts:166` | `<JobKanbanPage>` lê `searchParams.section` e passa pro manager |
| `JobStatusModal` com modes `pause/activate/cancel` + callbacks | `src/components/modals/job-status-modal.tsx:24-66` | Phase A: wirar direto |
| `JobPublishModal` com `onUnpublish` opcional | `src/components/modals/job-publish-modal.tsx:37-55` | Phase A: wirar; backend `/unpublish` em Phase C |
| `VALID_JOB_STATUSES` com `Cancelada` | `lia-agent-system/app/api/v1/job_vacancies/_shared.py:66` | Phase C: só consolidar drift em `crud.py:902` |
| `run_batch` aceita `[single_id]` | `app/domains/job_management/services/job_readiness_service.py:333` | Phase C: NÃO precisa criar `/enrich` single |
| i18n keys `vacancyCard.openWizard/openEnrichment/openWsi/etc.` | `messages/pt-BR.json:1677` | Phase A: reusar 80% das labels |
| `dispatch_screening` aceita `audience_policy` (3 valores: `new_only`, `imported_untriaged`, `manual_selection`) | `job_readiness_service.py:71` | Default `"new_only"` no CTA preview |
| Tool registry pattern `_wrap_*` | `wizard_tool_registry.py:319+` | Phase E: seguir convenção |
| Gupy + Pandapé têm `list_jobs()` | `ats_clients/{gupy,pandape}.py:323/333` | Phase D: import direto pra esses 2 |
| `IntentClassifier` com 5 intents fixos | `app/domains/ai/services/intent_classifier.py` | Phase E: NÃO adicionar tipos novos; ReAct loop pega tools por description |

### 3.2 🔴 Gaps reais a fechar

| Bug / Gap | Onde | Phase |
|---|---|---|
| Whitelist drift: `crud.py:902` rejeita `Cancelada` | `app/api/v1/job_vacancies/crud.py:902` | **C** (consolidar) |
| Endpoint `/unpublish` NÃO existe (só `/publish`) | `lifecycle.py` | **C** (criar) |
| Merge ATS sem `list_jobs()` | `merge.py` | **D** parcial — limitar UI a Gupy + Pandapé |
| `JobKanbanPage` não lê `searchParams.tab/section` no mount | `useKanbanPageCore.ts:102` (Zustand) | **A** (sync URL ↔ store) |
| Preview lateral de vaga não existe | n/a — criar do zero | **A** |
| Wizard não tem 4 tools (questions/dispatch/publish/status) | `wizard_tool_registry.py` | **E** |
| Lint sensor de exhaustive `VacancyAction` enum não existe | n/a | **F** |
| `ReadinessHubPage.tsx` órfão (zero importers, zero tests) | `plataforma-lia/src/components/pages/jobs/readiness/` | **0** (deletar) |

### 3.3 Risk register

| Risco | Severidade | Mitigação |
|---|---|---|
| `audience_policy` enum desconhecido | Resolvido | Default `"new_only"`; chat permite override via Phase E |
| URL param não persiste em refresh (Zustand reseta) | Baixa | Sync bidireccional URL ↔ Zustand no mount + `router.replace` em changes |
| `JobPublishModal` espera `jobs: Array` (multi-select) | Baixa | Passar `[vacancy]` (array de 1) |
| `JobStatusModal` modo triplo precisa decidir antes de abrir | Baixa | `getVacancyAction` retorna `kind` + `mode` discriminado |
| `run_batch` dedupe 300s pode bloquear cliques rápidos | Baixa | Toast "Ação em andamento" se response retorna `skipped_human_required` |
| Merge users → CTA "ATS direto" mostra falsa promessa | Média | Phase D detecta provider; se `merge`, disabled state com tooltip |
| Whitelist drift `crud.py:902` rejeita Cancelada hoje | Alta | Phase C consolida via import `from ._shared import VALID_JOB_STATUSES` + test pinning |

---

## 4. Faseamento

### Phase 0 — Cleanup (10 min)

**Deletar** `plataforma-lia/src/components/pages/jobs/readiness/ReadinessHubPage.tsx` + verificar zero importers (já confirmado órfão).

Commit: `chore(jobs): remove orphan ReadinessHubPage (replaced by chat-driven wizard)`

---

### Phase A — Vacancy Preview + deep-link + actions wired (~4h)

**Objetivo:** clicar num card abre painel lateral; CTAs por estágio navegam pra `/jobs/{id}?tab=edit&section=<X>` ou disparam ação direta (modal inline / API).

**Arquivos modificados:**

`plataforma-lia/src/components/pages/pipeline-overview-page.tsx`:
- Adicionar state `previewVacancy`, `showVacancyPreview`, `vacancyDetail` (lazy fetch).
- Handlers `handleOpenVacancyPreview / handleCloseVacancyPreview / handleNavigateVacancyPreview` espelhando candidate handlers (linhas 397-407).
- Substituir `getVacancyCta` (linha 205) por `getVacancyAction(stageKey, status, approval_status, t)` retornando union discriminada `VacancyAction`.
- Adicionar `<VacancyPreview>` JSX irmão de `<CandidatePreview>` (linha 769-780).
- `<PipelineVacancyCard>` (linha 1144): trocar `<a href>` + `window.open` por `<button onClick={() => onOpenPreview(vacancy)}>`.
- Mount conditional: `{showVacancyPreview && previewVacancy && <VacancyPreview ... />}` (defesa em profundidade rules-of-hooks).
- Mount inline: `{showPublishModal && <JobPublishModal jobs={[previewVacancy]} ... />}` e idem `<JobStatusModal>`.

`plataforma-lia/src/components/pages/job-kanban-page.tsx`:
- Ler `useSearchParams()` no mount → dispatch `useKanbanStore.setActiveTab(searchParams.tab || 'management')`.
- Passar `_externalActiveSection={searchParams.get('section') || undefined}` pro `<ScreeningConfigManager>` quando `tab='edit'`.
- Sync de volta: ao trocar tab/section via UI, `router.replace('/jobs/{id}?tab=edit&section=descricao')`.

**NOVO** `plataforma-lia/src/components/vacancy-preview/vacancy-preview.tsx` — painel lateral (`w-[420px]`):
- Header: título, departamento, location, work_model, seniority, ATS source badge.
- Status timeline (`stage_entered_at`, `updated_at`).
- Manager + candidate count + ATS metadata.
- Footer: 1-2 CTAs primárias do estágio via `getVacancyAction`.
- Lazy fetch detail via `liaApi.getJobVacancy(id)` ao abrir; skeleton enquanto carrega.
- Esc to close, focus trap, prev/next.
- **Hooks acima do early return** (regressão sensor `ae2e359b4`).

**NOVO** `plataforma-lia/src/services/lia-api/vacancy-actions-api.ts` — dispatchers tipo-seguros pro `VacancyAction`:

```ts
export type VacancyAction =
  | { kind: 'open-jd-config'; vacancyId: string }              // → /jobs/{id}?tab=edit&section=descricao
  | { kind: 'open-questions-config'; vacancyId: string }       // → /jobs/{id}?tab=edit&section=perguntas
  | { kind: 'open-roteiro-config'; vacancyId: string }         // → /jobs/{id}?tab=edit&section=configuracoes
  | { kind: 'dispatch-screening'; vacancyId: string }          // → POST dispatch (audience='new_only')
  | { kind: 'open-publish-modal'; vacancy: JobLifecycleVacancy }  // → <JobPublishModal>
  | { kind: 'open-status-modal'; vacancy: JobLifecycleVacancy; mode: 'pause'|'activate'|'cancel' }
  | { kind: 'noop' }                                            // encerrada
```

**Mapping por estágio (`getVacancyAction`):**

| Stage | Action.kind | Label (i18n) |
|---|---|---|
| `ats_importada` | `open-jd-config` | Reusar `vacancyCard.openWizard` ("Continuar JD") |
| `rascunho` | `open-jd-config` | `vacancyCard.openWizard` |
| `enriquecida` | `open-questions-config` | `vacancyCard.openEnrichment` ("Continuar enriquecimento") |
| `wsi_config` | `open-questions-config` | `vacancyCard.openWsi` ("Configurar WSI") |
| `aguardando_aprovacao` | `dispatch-screening` | `vacancyCard.openApproval` ("Revisar aprovação") |
| `publicada` | `open-publish-modal` | `vacancyCard.openPublish` ("Publicar vaga") |
| `ao_vivo` | `open-status-modal` (mode='pause') | NEW key `vacancyCard.openStatus` ("Alterar status") |
| `encerrada` | `noop` | `vacancyCard.openClosed` ("Ver encerramento") — disabled |

**TDD primeiro:**

`src/components/vacancy-preview/__tests__/vacancy-preview.test.tsx`:
- Renderiza CTA correto por estágio (table-driven 8 stages).
- Toggle isOpen false → true → false sem `throw` (regressão hooks).
- Esc fecha; backdrop fecha; prev/next funciona.

`src/services/lia-api/__tests__/vacancy-actions-api.test.ts`:
- Cada `kind` chama URL/endpoint correto.
- Exhaustive check `VacancyActionKind` no compile-time (assertNever).

`src/components/pages/__tests__/pipeline-overview-page.test.tsx` add:
- Clicar em card NÃO chama `router.push` direto; abre estado preview.

`src/components/pages/__tests__/job-kanban-page.test.tsx`:
- searchParams `?tab=edit&section=descricao` ativa tab + section corretas.

**Acceptance:**

- [ ] Clicar card abre preview lateral (sem nav direta pro kanban).
- [ ] Preview: skeleton → conteúdo após `getJobVacancy`.
- [ ] Prev/next + esc + backdrop OK.
- [ ] CTA `ats_importada/rascunho` → `/jobs/{id}?tab=edit&section=descricao` (page do screenshot do Paulo abre direto).
- [ ] CTA `enriquecida/wsi_config` → `/jobs/{id}?tab=edit&section=perguntas`.
- [ ] CTA `aguardando_aprovacao` → POST dispatch-screening (audience=new_only) → toast → refetch → vaga move estágio.
- [ ] CTA `publicada` → `<JobPublishModal>` abre inline.
- [ ] CTA `ao_vivo` → `<JobStatusModal>` abre inline (mode default `pause`).
- [ ] ESLint rules-of-hooks 0 violations.

**Commits:**
- `feat(jobs): add vacancy side-panel preview mirroring candidate flow`
- `feat(jobs): wire stage-aware actions with deep-link to configurações tab`
- `feat(jobs): support tab+section URL params in JobKanbanPage`
- `test(jobs): TDD coverage for vacancy preview + action dispatchers`

---

### Phase C — Backend gap closure (TDD-first) (~3h)

**Mudanças backend (TDD primeiro):**

1. `app/api/v1/job_vacancies/crud.py:902` — substituir whitelist hardcoded por `from ._shared import VALID_JOB_STATUSES`. Validar transição: `Cancelada` é terminal (não admite saída).

2. `app/api/v1/job_vacancies/lifecycle.py` — adicionar `POST /job-vacancies/{id}/unpublish` simétrico ao `/publish`. Body: `{}`; limpa `published_*` flags + `last_published_at`. `_require_company_id`.

3. `app/api/v1/ats.py` — adicionar `GET /ats/connections/{connection_id}/jobs`:
   - Valida connection ⊂ company_id (404, não 403).
   - Despacha pro client (`gupy`, `pandape`) via `.list_jobs()`.
   - Normaliza shape pra `{external_id, title, department, status, posted_at}`.
   - Cache 60s in-memory por (company_id, connection_id).
   - Para `merge` retorna 501 com `{error: 'list_jobs not implemented for merge yet'}`.

4. ADR-001: rotas só fazem auth + DTO; service chama repo. Adicionar `JobVacancyRepository.update_status` (se faltar); `AtsConnectionRepository.list_remote_jobs(connection_id, company_id)`.

**TDD:**

- `tests/api/test_job_vacancy_status_cancelada.py` — Cancelada de `Ativa` ✓; de `Rascunho` ✗ 422; depois de `Cancelada` qualquer transição ✗ (terminal).
- `tests/api/test_job_vacancy_unpublish.py` — happy; idempotent; audit event.
- `tests/api/test_ats_list_jobs.py` — cross-tenant 404; normalizado para Gupy/Pandapé.
- `tests/api/test_status_whitelist_consolidation.py` — `crud.py` e `lifecycle.py` usam mesma fonte.

**Commits:**
- `fix(api): consolidate VALID_JOB_STATUSES (crud.py + lifecycle.py)`
- `feat(api): add unpublish endpoint symmetric to publish`
- `feat(api): add list-remote-jobs endpoint per ATS connection`

---

### Phase D — BulkImportModal direct ATS import (~9h)

**Mudanças frontend:**

`plataforma-lia/src/components/jobs/BulkImportModal.tsx`:
- Adicionar tabs `[CSV] [JSON] [ATS Conectado]` no topo.
- Default tab = última usada (localStorage).
- Hooks acima do early return (regressão sensor).

**NOVO** `src/components/jobs/bulk-import/AtsImportTab.tsx`:
- Step 1: lista connections via `GET /api/backend-proxy/ats/connections`.
  - Para Merge: card com tooltip "Em breve" + link pra Settings.
- Step 2: clicar connection (Gupy/Pandapé) → fetch `/api/backend-proxy/ats/connections/{id}/jobs`. Virtualizar lista (>50 jobs); checkbox por job; search/filter.
- Step 3: confirmar → POST `/api/backend-proxy/ats/connections/{id}/sync` com body `{job_ids: [...]}`.

**NOVO** proxy `src/app/api/backend-proxy/ats/connections/[connectionId]/jobs/route.ts`.

Reusar `useAtsIntegrations` hook.

**TDD:**

`BulkImportModal.test.tsx` add:
- 3 tabs renderizadas.
- Tab ATS lista connections.
- Selecionar connection carrega jobs.
- Multi-select + import dispatcha endpoint.
- Hooks acima do early return.
- Merge connection mostra disabled tooltip.

**Acceptance:**
- [ ] Recrutador conecta Gupy → BulkImportModal → tab "ATS" → vê suas vagas Gupy → seleciona 3 → importa → 3 vagas em `ats_importada` na rail.
- [ ] CSV e JSON tabs continuam funcionando idênticas.
- [ ] Merge: tooltip "Em breve".

**Commits:**
- `feat(jobs): add ATS direct import tab to BulkImportModal`
- `feat(api-proxy): add ATS connection jobs proxy route`

---

### Phase E — Wizard chat awareness (~12h)

**Mudanças backend:**

`app/domains/job_management/tools/job_wizard_tools.py` — adicionar 4 funções:
- `generate_screening_questions(vacancy_id, company_id, mode='compact'|'complete')` → service que chama `wsi/generate-questions`.
- `dispatch_screening(vacancy_id, company_id, audience_policy='new_only')`.
- `publish_vacancy(vacancy_id, company_id)` / `unpublish_vacancy(vacancy_id, company_id)`.
- `change_vacancy_status(vacancy_id, company_id, status)` — incluindo Cancelada (Phase C).

`app/domains/job_management/agents/wizard_tool_registry.py` — registrar 4 `ToolDefinition`:

```python
ToolDefinition(
    name="generate_screening_questions",
    description="Gera perguntas de triagem WSI (compacta=5, completa=15) para uma vaga.",
    parameters={
        "type": "object",
        "properties": {
            "vacancy_id": {"type": "string", "description": "ID da vaga"},
            "mode": {"type": "string", "enum": ["compact", "complete"], "description": "compacta=5, completa=15"},
        },
        "required": ["vacancy_id", "mode"],
    },
    output_schema=ToolOutput,
    function=_wrap_generate_screening_questions,
)
# ... análogo para dispatch/publish/unpublish/change_status
```

Cada tool:
- `company_id` from agent context (NUNCA do payload).
- Validate vacancy ⊂ company_id antes de chamar service.
- Pydantic schema para args (rejeita LLM hallucinated values).

**Stage allowlist:** registrar `allowed_stages: list[str]` por tool. ReAct loop só oferece a tool se vaga está em estágio compatível. Sensor introspection.

**Fairness/LGPD:** question-generation tool DEVE injetar fairness preamble (zero raça/religião/gênero/idade). Sensor regex check no output.

**TDD:**
- `test_wizard_tools_generate_questions_compact_5_complete_15.py`
- `test_wizard_tool_rejects_cross_tenant_vacancy_id` (parametrizado over 4 tools).
- `test_react_loop_only_offers_dispatch_when_aguardando_aprovacao`.
- `test_question_generation_prompt_contains_fairness_block`.
- `test_llm_hallucinated_status_value_rejected_by_pydantic`.
- `test_tool_introspection_every_tool_has_allowed_stages` (sensor).

**Acceptance:**
- [ ] "ativa a triagem da vaga de Engenheiro de Dados" → wizard identifica + confirma + dispatcha.
- [ ] "criar triagem compacta pra vaga X" → 5 perguntas no painel lateral.
- [ ] "criar triagem completa" → 15 perguntas.
- [ ] Cross-tenant vacancy_id sempre rejeitado.

**Commits:**
- `feat(wizard): register 4 stage-action tools (questions/dispatch/publish/status)`
- `feat(wizard): stage allowlist + fairness preamble in tools`
- `test(wizard): tenant isolation + stage allowlist + fairness sensor`

---

### Phase F — Harness sensors + governança (~3h)

**Mudanças:**

1. `~/.claude/CLAUDE.md` (global) — adicionar seção "Vacancy preview canonical pattern":
   - Referenciar `pipeline-overview-page.tsx:307-308, 397-407, 769-780`.
   - Boy-Scout: novo CTA de vaga deve estender `VacancyActionKind`.
   - Deep-link convention: `/jobs/{id}?tab=edit&section={configuracoes|descricao|perguntas}`.

2. **NOVO** `lia-agent-system/scripts/check_company_id_in_routes.py` — AST-walk `app/api/v1/*.py`, falha se rota não chama `_require_company_id`.

3. **NOVO** `plataforma-lia/scripts/check-vacancy-action-coverage.ts` — TS AST sensor que parseia `getVacancyAction` e garante 8 estágios têm branch.

4. Estender `.github/workflows/frontend-ci.yml` — adicionar steps pra ambos sensores.

5. E2E (Playwright) `e2e/vacancy-preview.spec.ts` — happy path por estágio.
   `e2e/bulk-import-ats.spec.ts` pra Phase D.

6. ADR `docs/adr/ADR-007-vacancy-preview-mirror.md` — codifica padrão.

**Acceptance:**
- [ ] 4 sensores em CI; PR bloqueado se algum falhar.
- [ ] CLAUDE.md com seção e exemplos.
- [ ] E2E verde local.

**Commits:**
- `chore(governance): document vacancy preview canonical pattern in CLAUDE.md`
- `chore(ci): add AST sensors for company_id and vacancy action coverage`
- `test(e2e): playwright happy paths for vacancy preview + bulk import ATS`

---

## 5. Reuse — utilitários existentes

- `src/components/candidate-preview.tsx` — padrão de painel lateral (props, focus trap, navegação).
- `src/services/lia-api/jobs-api.ts` — `getJobVacancy`, `updateJobVacancyStatus` (já implementados, 21.5KB).
- `src/services/lia-api/candidates-api.ts` — padrão pra mirror em `vacancy-actions-api.ts`.
- `src/components/screening-config/ScreeningConfigManager.tsx` — `SCREENING_SECTIONS` + `_externalActiveSection`.
- `src/components/pages/job-kanban/KanbanJobHeader.tsx:316-345` — tabs `management` / `edit`.
- `src/components/modals/job-publish-modal.tsx` (714 linhas) + `job-status-modal.tsx` (287 linhas) — reusar inline.
- `app/domains/ats_integration/services/ats_clients/{gupy,pandape}.py:list_jobs()` — já implementados.
- `app/api/v1/job_readiness.py` services — reusar via thin wrappers em wizard tools.
- `app/api/wsi/questions.py` — reusar; mode auto-detect.
- Hook `useAtsIntegrations` — reusar pra Phase D.
- i18n keys `pipelineOverview.vacancyCard.*` em `messages/pt-BR.json:1677` — reusar 80%.

## 6. Não-mexer (READ-ONLY / canonical)

- `lia-agent-system/libs/models/lia_models/` — schemas estáveis; alterações via migration (CLAUDE.md REGRA 5).
- `ats-api-copia/` — Rails canônico (CLAUDE.md READ-ONLY).
- `edit-job-modal.tsx` (718 linhas, sections vagas básicas) — não mexer; é outro modal não relacionado.
- `BulkImportModal.tsx` recém-consertado — só extender com tab nova; preservar fix rules-of-hooks (commit `7c24ece9a`).
- `ScreeningConfigManager.tsx` — não mexer estrutura; consumir via `_externalActiveSection`.
- `job-publish-modal.tsx` (714 linhas) — reusar inline; não refatorar.
- `job-status-modal.tsx` (287 linhas) — reusar inline; não refatorar.

---

## 7. Verification (E2E)

### Por fase, antes do commit final:

**Frontend:**
```bash
ssh -i ~/.ssh/replit -p 22 -o StrictHostKeyChecking=no <REPLIT_HOST> \
  'cd /home/runner/workspace/plataforma-lia && \
   timeout 300 npx eslint src --no-color 2>&1 | grep -cE "rules-of-hooks" && \
   timeout 120 npx vitest run --project=components <test-glob>'
```
Esperar: `0` rules-of-hooks + tests verdes.

**Backend:**
```bash
ssh ... 'cd /home/runner/workspace/lia-agent-system && \
   timeout 120 python -m pytest tests/<phase-tests>/ --no-cov -q'
```

### Manual UI smoke (Phase A) — Paulo no browser:

1. `/recrutar` → toggle "Vagas".
2. Clicar card de qualquer estágio → preview lateral abre, sem nav direta pro kanban.
3. Esc fecha; backdrop fecha; prev/next navega.
4. `ats_importada` ou `rascunho`: clicar "Continuar JD" → URL muda pra `/jobs/{id}?tab=edit&section=descricao` (page do screenshot já aberta).
5. `enriquecida`: clicar "Continuar enriquecimento" → `/jobs/{id}?tab=edit&section=perguntas`. Recrutador escolhe compacta/completa lá.
6. `wsi_config`: clicar "Configurar WSI" → mesma section.
7. `aguardando_aprovacao`: clicar "Revisar aprovação" → POST dispatch (audience=new_only) → toast → refetch → vaga move pra `publicada`.
8. `publicada`: clicar "Publicar vaga" → `<JobPublishModal>` abre inline. Despublicar usa endpoint Phase C.
9. `ao_vivo`: clicar "Alterar status" → `<JobStatusModal>` inline (default `pause`). Cancelar funciona após Phase C.
10. `encerrada`: CTA disabled.

### Manual UI smoke (Phase D):
- BulkImportModal tab "ATS Conectado" → escolher Gupy → import 3 vagas seletivamente → aparecem em `ats_importada`.

### Manual UI smoke (Phase E):
- "ativa a triagem da vaga de Engenheiro de Dados" no chat → wizard identifica + confirma + dispatcha.
- "criar triagem completa pra vaga X" → 15 perguntas no painel lateral.

### Sensores harness (Phase F):
- CI passa em `check_company_id_in_routes.py` + `check-vacancy-action-coverage.ts` + ESLint rules-of-hooks + Playwright.

---

## 8. Ordem de execução

```
Phase 0 (delete ReadinessHubPage)            [10 min]
   ↓
Phase A (preview + deep-link + actions)       [4h] ── PARAR pra validação Paulo no browser
   ↓
Phase C (backend gaps + Cancelada drift)      [3h] ── tests verdes; Phase A toasts substituídos
   ↓
Phase D (ATS direct Gupy/Pandapé)             [9h] ── PARAR pra validação
   ↓
Phase E (wizard tools + chat awareness)       [12h] ── PARAR pra validação
   ↓
Phase F (harness sensors + governança)        [3h] ── CI green em tudo
```

**Total estimado: ~31h** (~4 dias focused).

**Checkpoint 1:** após Phase A — Paulo valida UI manualmente.
**Checkpoint 2:** após Phase D — Paulo valida fluxo ATS direto.
**Checkpoint 3:** após Phase F — sign-off final.

---

## 9. Constraints (CLAUDE.md golden rules — non-negotiable)

- **Multi-tenancy:** todo endpoint valida `company_id` do JWT, NUNCA do payload. Sensor F.
- **LGPD:** zero raça/religião/gênero/idade em decisões IA. Fairness preamble em question-generation.
- **Fairness:** prompts de ranking de candidatos com instruções de fairness explícitas.
- **No hardcoded secrets:** API keys via env vars.
- **Design tokens:** zero cores hardcoded; usar `lia-*`, `status-*`, `wedo-*`.
- **ADR-001 Repository Pattern:** services NÃO fazem SQL inline; cross-domain reads via repos.
- **Rules of Hooks:** hooks SEMPRE acima de early return em modais/components. Sensor F.
- **Branch ativa `feat/benefits-prv-canonical`:** sem novas branches; commits via SSH; push é responsabilidade do Paulo via Replit IDE.
- **Boy Scout:** P2 issues em arquivos modificados consertados no mesmo commit; P0/P1 fora do escopo reportados separadamente.
- **Harness Engineering:** todo defeito tem guide (regra/convenção) + sensor (test/lint/CI). Computacional sempre antes de inferencial.

---

## 10. Estado da execução

| Phase | Status | Commits | Notas |
|---|---|---|---|
| 0 | ✅ done | 1bd182c80 | ReadinessHubPage + ImportJobsDrawer deletados |
| A | ✅ done | 6a19f9234 + 9274ccdf0 | Preview lateral + deep-link + actions wired (12 tests) |
| C | ✅ done | d220e5958 | Whitelist drift + /unpublish + ATS list-jobs (16 tests) |
| D | ✅ done | cee68ab29 | BulkImportModal ATS tab + onUnpublish wired |
| E | ✅ done | 987a07a1b | 4 wizard tools + STAGE_TOOLS allowlist (10 tests) |
| F | 🟢 in progress | — | CLAUDE.md atualizada; AST sensors em andamento |

> Cada phase atualiza esta tabela ao concluir.
