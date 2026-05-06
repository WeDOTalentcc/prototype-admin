# Handoff — Dívida Residual (Phase H+)

**Branch ativa Replit:** `feat/benefits-prv-canonical`
**Plan canonical:** `.planning/vacancy-pipeline-plan.md`
**Governance:** `~/.claude/CLAUDE.md` > seções "Governança Git", "Frontend / React rules-of-hooks discipline", "Vacancy preview canonical pattern (2026-05-06)"
**Branch state em 2026-05-06:** Phase 0→H landed (commits `1bd182c80 → 5ecc35c4f`).

> Cada ticket abaixo é um prompt **auto-suficiente**. Pode jogar copy-paste em sessão nova do Claude — ele tem todo contexto pra executar. Antes de começar, sempre rodar: `git branch --show-current` e confirmar que está em `feat/benefits-prv-canonical` (REGRA 2 do CLAUDE.md).

---

## TICKET 1 — Auditar e fechar 1581 multi-tenancy gates

### Severidade
🟡 P1 — security correctness; alguns são IDOR reais (como `mark_pipeline_customized` e `company_culture.py` que já fixei), maioria são falsos positivos onde service layer faz scoping interno.

### Por que existe
A skill `harness-engineering` adicionou um sensor AST em `lia-agent-system/scripts/check_company_id_in_routes.py` que walks `app/api/v1/*.py` e marca como offender toda rota que não chama `_require_company_id` ou `get_user_company_id` no body. Quando rodei, encontrou **1588** offenders. Phase G fixou 1 (mark_pipeline_customized IDOR), Phase H fixou 7 (`company_culture.py`). Ainda restam **1581** offenders distribuídos em ~50 arquivos.

### Prompt para sessão nova

```
Estou em `feat/benefits-prv-canonical` no Replit. Preciso fazer audit + fix
dos 1581 routes flagged pelo sensor `lia-agent-system/scripts/check_company_id_in_routes.py`.

Contexto canônico:
- Multi-tenancy é golden rule #1 do CLAUDE.md: company_id sempre do JWT, nunca do payload.
- O sensor é warn-only por enquanto (continue-on-error: true em frontend-ci.yml).
- Após cleanup, mude pra --strict no CI step.

Trabalho per-arquivo (não tente o universo de uma vez):
1. SSH ao Replit, rode o sensor e agrupe offenders por arquivo:
   ```
   ssh replit-wedo 'cd lia-agent-system && python3 scripts/check_company_id_in_routes.py 2>&1 | grep -oE "app/api/v1/[a-z_/]+\.py" | sort | uniq -c | sort -rn | head -20'
   ```
2. Para cada arquivo, classifique cada rota em uma das 3 categorias:
   - **REAL BUG**: rota faz SQL/SELECT/UPDATE/DELETE com filter por id mas SEM company_id check.
     Padrão de fix: extract `company_id = get_user_company_id(current_user)` no topo, validar match
     contra payload/path company_id (404 cross-tenant), scope SQL pelo company_id.
   - **DELEGADO**: rota só chama service.do_something(request, current_user). Service internamente
     valida. Fix: adicione comentário `# multi-tenancy: scoping deferred to <service>.<method>`
     no body. O sensor reconhece e ignora.
   - **PUBLIC/SHARED**: rota é shared infrastructure (e.g. semantic_search expand_skills,
     trust_center public docs, archetypes catalog). Fix: comentário `# multi-tenancy: public
     read-only` ou `# multi-tenancy: shared infrastructure`.

3. Comece pelos arquivos COM MUTAÇÃO de DB (POST/PUT/DELETE/PATCH) — esses têm maior risco de
   ser real bug. Use:
   ```
   grep -nE "@router\.(post|put|delete|patch)" app/api/v1/<file>.py
   ```

4. Para cada fix, escreva um teste pytest que prova o cross-tenant retorna 404, não 200.
   Modelo canônico em `tests/api/test_unpublish_endpoint.py` (Phase C).

5. Quando todos offenders forem 0 ou marcados, mude
   `.github/workflows/frontend-ci.yml` step "Multi-tenancy gate sensor" pra remover
   `continue-on-error: true` e adicionar `--strict` na chamada.

Arquivos prioritários (alta probabilidade de IDOR real, baseado em nome):
- app/api/v1/company.py (843 analyze_company_culture)
- app/api/v1/company_culture_config.py (8 routes — culture profiles)
- app/api/v1/dashboard_data.py (5 routes — strategic indicators)
- app/api/v1/recruitment_stages/* (~15 routes — pipeline customization)
- app/api/v1/job_vacancies/analytics.py (lifecycle/aggregations)

Arquivos prováveis falso-positivo (delega a service / shared):
- app/api/v1/analysis.py (3 routes — AI analysis service)
- app/api/v1/semantic_search.py (8 routes — public expansion)
- app/api/v1/trust_center.py (14 routes — public docs)
- app/api/v1/wsi/* (já têm sensor de fairness — Phase H)

Validação por arquivo:
   pytest tests/api/test_<file>_*.py
   python3 scripts/check_company_id_in_routes.py | grep <file>  # deve retornar vazio

Validação final (depois de tudo):
   python3 scripts/check_company_id_in_routes.py --strict  # deve exit 0

Branch correta antes de tocar: feat/benefits-prv-canonical (CLAUDE.md REGRA 2).
Sem push (REGRA 4).
```

### Estimativa
~2-3 dias focused (50+ files × 5-15 min/file de leitura + 5 min/fix de código + 5 min de teste).

---

## TICKET 2 — Fix os 32 testes pré-existentes failing

### Severidade
🟢 P2 — todos em files que NÃO toquei; pré-existem desde antes do Phase 0. Tornam CI vermelho mas não bloqueiam funcionalidade.

### Por que existe
Phase H regenerou 40 snapshots (de 73 fails → 32). Os 32 restantes são **assertion failures reais** — o componente evoluiu mas o teste não foi atualizado. Distribuição:

| File | # fails |
|---|---|
| `chip.test.tsx` | 2 (token expectations: compact/comfortable density) |
| `KanbanCard.test.tsx` | 8 (component shape changed) |
| `automations-tab.test.tsx` | 1 |
| `CandidatesTableArea.test.tsx` | 5 |
| `CandidatesPageHeader.test.tsx` | 12 (renders empty — major regression in component) |
| `OfferReviewModal.test.tsx` | 2 |
| `WebhooksManager.test.tsx` | 2 |

### Prompt para sessão nova

```
Estou em `feat/benefits-prv-canonical` no Replit. Há 32 testes Vitest failing
distribuídos em 7 files. Todos são pré-existentes (não introduzidos por
nenhum commit recente — predate o Phase 0). Quero diagnosticá-los e
consertar caso a caso.

Branch ativa: feat/benefits-prv-canonical (REGRA 2 CLAUDE.md). Sem push (REGRA 4).

Comece pelo arquivo CandidatesPageHeader.test.tsx — 12/12 testes falham,
provavelmente todos pelo mesmo root cause (render fail). Se for um único
fix, resolve 12 de uma vez.

Para cada arquivo, em ordem (CandidatesPageHeader, CandidatesTableArea,
KanbanCard, OfferReviewModal, WebhooksManager, automations-tab, chip):

1. Rode só esse arquivo:
   ssh replit-wedo 'cd plataforma-lia && timeout 60 npx vitest run --project=components <path> 2>&1 | tail -50'

2. Leia o componente correspondente em src/components/...

3. Categorize:
   - **Component changed (rendering selector mismatch)**: teste procura
     `text="Funil de Talentos"` mas componente renderiza outro texto.
     Fix: atualizar selector ou regenerar ass via `vitest -u <file>`.
   - **Component broke (real regression)**: render lança erro.
     Fix: investigar o componente; pode ser bug introduzido por
     refactor anterior. Reportar issue separada se for grande.
   - **Test setup outdated (mock/fixture)**: teste mocka API que
     mudou de signature.
     Fix: atualizar mock.

4. Aplique fix. Rode o file só pra ver:
   timeout 60 npx vitest run --project=components <file>

5. Quando todos 32 estiverem verdes, rode o suite completo pra confirmar
   nada regrediu:
   timeout 300 npx vitest run --project=components --project=unit-colocated

Importante: não use `vitest -u` indiscriminadamente nesses files —
dos 73 fails, 40 foram resolvidos com -u (snapshot drift legítimo) na
Phase H. Os 32 restantes NÃO são snapshot fails, então `-u` esconderia
o problema sem corrigir.

Ordem sugerida (mais impacto primeiro):
  1. CandidatesPageHeader (12 fails)
  2. KanbanCard (8 fails)
  3. CandidatesTableArea (5 fails)
  4. OfferReviewModal (2)
  5. WebhooksManager (2)
  6. chip (2 token tests)
  7. automations-tab (1)
```

### Estimativa
~3-5 horas (cada arquivo precisa lerd o componente + atualizar teste).

---

## TICKET 3 — E2E Playwright happy path para Vacancy Preview

### Severidade
🟢 P2 — Vitest smoke já cobre regressão crítica (15 tests), mas E2E pega problemas de integração (auth, routing real, API real).

### Por que existe
Phase A.2 escreveu Vitest smoke pro `<VacancyPreview>` (12 tests). Phase F mencionou E2E Playwright como follow-up; foi punted por causa de fixtures setup pesado.

### Prompt para sessão nova

```
Estou em `feat/benefits-prv-canonical`. Quero adicionar E2E Playwright
para o fluxo "Recrutar > Vagas > preview lateral > deep-link Configurações"
implementado em Phase A (commits 6a19f9234, 9274ccdf0).

Estrutura existente:
- plataforma-lia/e2e/tests/job-creation/01-modal-creation.spec.ts (modelo)
- plataforma-lia/e2e/fixtures/job-creation.fixture.ts (auth + helpers)

Crie e2e/tests/vacancy-preview/01-stage-actions.spec.ts cobrindo:

  1. Setup: navegar pra /recrutar, toggle mode "Vagas".
  2. Por estágio na rail (ats_importada, enriquecida, aguardando_aprovacao,
     publicada, ao_vivo), assert:
     - Rail card visível para o estágio
     - Click no card abre side panel (selector: [aria-label*="Visualizar vaga"])
     - Side panel tem o CTA correto:
        ats_importada/rascunho → "Continuar JD"
        enriquecida → "Continuar enriquecimento"
        wsi_config → "Configurar WSI"
        aguardando_aprovacao → "Revisar aprovação"
        publicada → "Publicar vaga"
        ao_vivo → "Alterar status"
  3. Click "Continuar JD" → URL muda para /jobs/<id>?tab=edit&section=descricao
     E a tab "Configurações" + section "Descrição do Cargo" abrem.
  4. Click ESC fecha o painel.

Setup mínimo necessário:
  - Auth fixture (já existe em e2e/fixtures/job-creation.fixture.ts)
  - Test data: necessita de pelo menos 1 vaga em cada um dos 6 estágios
    com candidatos. Use a mesma seed que job-creation.fixture usa, ou
    crie uma nova helper que cria 6 vagas dummy via API antes do teste.

Validação: rodar o spec e ver tudo passar.
  ssh replit-wedo 'cd plataforma-lia && npx playwright test e2e/tests/vacancy-preview/'

Importante: este teste vai contra o backend real do Replit dev server.
Garanta que o servidor está running antes (porta 5000 default).
```

### Estimativa
~4-6 horas (test data setup + 6 cases + flake-proofing).

---

## TICKET 4 — i18n migration de BulkImportModal hardcoded strings

### Severidade
🟢 P3 — só relevante quando produto for traduzido pra EN. Hoje todo o app é PT-BR.

### Por que existe
Phase D adicionou tab "ATS Conectado" no BulkImportModal mas usou string hardcoded (igual aos labels CSV/JSON existentes). Não migrei pra i18n por seguir o style existente.

### Prompt para sessão nova

```
Quero migrar todos os strings hardcoded do BulkImportModal pra i18n
usando next-intl (já configurado em plataforma-lia/src/i18n/).

Strings a migrar (todos em src/components/jobs/BulkImportModal.tsx):
  - "Importar vagas do ATS"
  - "Arquivo CSV"
  - "Colar JSON"  
  - "ATS Conectado"
  - todos os textos descritivos do CSV/JSON paths
  - error messages tipo "JSON vazio ou sem 'jobs'"

E em src/components/jobs/bulk-import/AtsImportTab.tsx:
  - todos os labels (Carregando integrações, Configurar uma agora, etc)

Steps:
1. Adicione namespace "bulkImport" em messages/pt-BR.json e messages/en.json:
   {
     "bulkImport": {
       "title": "Importar vagas do ATS" / "Import jobs from ATS",
       "tabs": { "csv": "Arquivo CSV" / "CSV file", ... },
       ...
     }
   }

2. No componente: useTranslations('bulkImport') no topo.

3. Substituir cada string literal pelo t('chave').

4. Smoke test: timeout 60 npx vitest run BulkImportModal AtsImportTab

5. Lint: timeout 60 npx eslint src/components/jobs/

Branch: feat/benefits-prv-canonical (atual).
```

### Estimativa
~2 horas.

---

## TICKET 5 — Switch multi-tenancy sensor para --strict no CI

### Severidade
🟢 P2 — ativa o gate só DEPOIS do TICKET 1 estar resolvido.

### Por que existe
Atualmente .github/workflows/frontend-ci.yml roda o sensor com `continue-on-error: true` (warn-only) por causa dos 1581 offenders pré-existentes. Quando todos forem fixados ou anotados (TICKET 1), o sensor deve virar gate real.

### Prompt para sessão nova

```
Pré-requisito: TICKET 1 deve estar resolvido (zero offenders ou todos
anotados com `# multi-tenancy: <reason>`).

Verifique: 
  ssh replit-wedo 'cd lia-agent-system && python3 scripts/check_company_id_in_routes.py --strict; echo "exit=$?"'
  
  Se exit=0, prossegue. Se exit=1, volte ao TICKET 1.

Edit .github/workflows/frontend-ci.yml step "Multi-tenancy gate sensor":
  - Remova `continue-on-error: true`
  - Adicione `--strict` na chamada do script:
    `python3 scripts/check_company_id_in_routes.py --strict`
  - Atualize o comentário do step refletindo que agora bloqueia.

Commit:
  chore(ci): promote multi-tenancy sensor to strict mode after TICKET 1 cleanup
```

### Estimativa
~5 minutos (após TICKET 1 fechar).

---

## Ordem sugerida

1. **TICKET 2** primeiro (testes failing) — limpa o ruído do CI sem risco; ~3-5h.
2. **TICKET 3** (E2E) — cobre o trabalho recente; ~4-6h.
3. **TICKET 4** (i18n) — quando precisar suporte EN; ~2h.
4. **TICKET 1** (multi-tenancy) — peça canonical, mas é o trabalho maior; ~2-3 dias.
5. **TICKET 5** (--strict CI) — após 1; ~5 min.

Total estimado se fizer tudo: ~3-4 dias focados.

---

## Comandos de orientação úteis em qualquer sessão

```bash
# Confirmar branch
ssh replit-wedo 'cd /home/runner/workspace && git branch --show-current'
# → deve retornar feat/benefits-prv-canonical

# Re-rodar todos sensors:
ssh replit-wedo 'cd plataforma-lia && timeout 60 npx tsx scripts/check-vacancy-action-coverage.ts'
ssh replit-wedo 'cd lia-agent-system && python3 scripts/check_company_id_in_routes.py 2>&1 | tail -3'

# Re-rodar tests Phase A-H:
ssh replit-wedo 'cd plataforma-lia && timeout 90 npx vitest run --project=components src/components/vacancy-preview src/components/jobs/__tests__/BulkImportModal.test.tsx'
ssh replit-wedo 'cd lia-agent-system && timeout 60 python -m pytest tests/api/test_status_whitelist_consolidation.py tests/api/test_unpublish_endpoint.py tests/api/test_ats_list_jobs_normalization.py tests/wizard/test_phase_e_wizard_tools.py tests/wsi/test_fairness_bias_markers.py --no-cov -q'

# Ver o plan canonical:
ssh replit-wedo 'cat /home/runner/workspace/.planning/vacancy-pipeline-plan.md'
```
