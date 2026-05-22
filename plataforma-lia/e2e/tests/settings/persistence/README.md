# E2E Persistence Tests — Configurações

> Status: **Wave 1 — subset crítico (Minha Empresa + Learning Loops + Schedule)**
> Origem: gap original do pedido Paulo 2026-05-21 ("verificar persistência de
> cada campo de cada sessão e subssessão"). Auditoria estática foi feita; este
> pacote fecha o gap browser-level.

## Por que existem?

Sensors existentes (ADR-001 sensors, `tests/contract/test_*_gate.py`, lint
scripts) cobrem o **write path** — schema correto, gate fail-closed, multi-
tenancy. Eles **não comprovam o round-trip**: campo persistiu no BD E voltou
no GET subsequente? Bugs típicos que escapam dos sensors estáticos:

1. **PATCH 200 + GET vazio** — serializer Pydantic com `exclude_unset` muito
   agressivo (vide T1017 `convert_none_to_false`).
2. **State local React stale** — toggle parecia salvar mas voltou OFF no
   reload (audit menu_configuracoes_inteligencia_agentes.md 2026-05-21).
3. **Ghost setting** — UI tinha toggle SEM consumer agente. Persistence funcionava
   mas mudança era inerte. Cobre-se aqui com pareamento: persiste? Then a
   contract test separado garante consumer existe.

## Como rodar local (Replit ou Mac)

```bash
# Replit: backend já está em pé na 8001, frontend em 5000
cd /home/runner/workspace/plataforma-lia
npm run test:e2e -- e2e/tests/settings/persistence/

# Mac local: assume staging
cd plataforma-lia
PLAYWRIGHT_BASE_URL=https://staging.wedotalent.cc \
  DEV_AUTO_LOGIN_EMAIL=demo@wedotalent.com \
  DEV_AUTO_LOGIN_PASSWORD=demo123 \
  npx playwright test e2e/tests/settings/persistence/
```

## Como rodar um único spec

```bash
npx playwright test e2e/tests/settings/persistence/learning-loops-persistence.spec.ts
```

## Tag de filtro

Todos os tests de round-trip estão taggeados `@persistence`:

```bash
npx playwright test --grep @persistence
```

## Pattern canonical pra adicionar test novo

1. **Identificar o campo/toggle/seção** a testar. Confirmar que o backend
   tem endpoint REST correspondente (PATCH/POST) e que GET subsequente
   retorna o campo.
2. **Localizar o selector** no componente React:
   * Preferência 1: `data-testid="<canonical-key>"` — adicionar se ainda não
     existe (vide TODO na seção abaixo).
   * Preferência 2: `role="switch"` + `aria-label="<label visível>"` para
     toggles (pattern `LearningLoopsPanel.ToggleSwitch`).
   * Last resort: heading text + heurística de "primeiro input visível" no
     card-mãe. Marcar TODO no test.
3. **Escolher helper canonical**:
   * `assertSwitchPersistsAfterRefresh(page, ariaLabel)` — toggles
   * `assertInputPersistsAfterRefresh(page, input, saveBtn, value)` — inputs editáveis
4. **Restore state** no fim do test (`restoreSwitch` ou re-fill com valor
   original) — tests serializados (workers: 1, fullyParallel: false) mas
   mesmo assim NÃO devem deixar drift no tenant demo.
5. **Taggear** `@persistence` no título do test.

## Cobertura atual (Wave 1)

| Hub / Sub | Tests | Helpers usados |
|-----------|-------|----------------|
| Minha Empresa — basic | 1 | `assertInputPersistsAfterRefresh` |
| Minha Empresa — mission | 1 | `assertInputPersistsAfterRefresh` |
| Minha Empresa — smoke render | 1 | – |
| Learning Loops — master | 1 | `assertSwitchPersistsAfterRefresh` |
| Learning Loops — 4 sub-toggles | 4 (parametric) | `assertSwitchPersistsAfterRefresh` |
| Comunicação — Schedule (respect_weekends) | 1 | manual |
| Comunicação — Schedule (sending_hours_start) | 1 | manual |
| Comunicação — Schedule smoke | 1 | – |

**Total Wave 1: ~11 tests.**

## Próximas waves (backlog)

- **Wave 2** — Governança (7 sub-panels: hiring_policy, communication_rules,
  manager_preferences, signature, NPS, automations, recruitment_journey)
- **Wave 3** — Fairness Compliance (4 sub-sessões + 34 `lia_field_toggles`)
- **Wave 4** — Pipeline + Screening (rubric, calibration, screening_question_set)
- **Wave 5** — Templates + Signature + ABTesting
- **Wave 6** — Usuários + Departamentos
- **Wave 7** — Integrations (Apify, HubSpot, BYOK)
- **Wave 8** — AI Credits + Webhooks

## TODOs canonical no frontend (harness gap)

Os tests acima funcionam HOJE com selectors heurísticos (texto/role). Para
aumentar robustez e reduzir manutenção:

1. `MinhaEmpresaCard.tsx:144` — input edit-in-place precisa de
   `data-field="<canonical_key>"` (e.g. `company_name`, `mission`,
   `tech_stack`).
2. `ScheduleTab.tsx` — toggles e number inputs precisam de
   `data-testid="schedule-{respect-weekends,respect-holidays,sending-hours-start,sending-hours-end,max-messages-per-day}"`.
3. `LearningLoopsPanel.tsx:106` — adicionar `data-testid="toggle-{def.key}"`
   complementar ao `aria-label` (label muda com i18n; key é estável).
4. Sub-tabs de hubs com múltiplos painéis (Learning Loops, Comunicação,
   Governança) precisam de `data-testid="settings-subtab-{key}"`.

Quando esses TODOs forem fechados, simplificar os helpers em `test-utils.ts`
pra dropar fallbacks heurísticos.

## Failure modes conhecidos

| Sintoma | Causa provável |
|---------|----------------|
| `test.skip — Bloco "basic" já está 100% preenchido` | Demo data sem pendências. Rodar `scripts/seeds/demo_company --reset`. |
| `[setup] switch "X" não está visível` | i18n mudou label OU sub-tab não foi montada. Verificar fixture `navigateToSettings` e label canonical. |
| `[persistence FAIL] valor não preservado após reload` | **Bug real** — investigar PATCH/GET round-trip. Comparar com sentinels `tests/integration/agents/test_*_roundtrip*.py`. |
| `[regression] switch sumiu após reload` | Component crash pós-PATCH OR conditional render mudou (`is_active` flag). |

## CI integration

Workflow `lia-agent-system/.github/workflows/ci.yml` recebeu job
`e2e-persistence` que roda este pacote contra staging em PRs touching:
- `lia-agent-system/app/domains/*/services/*.py`
- `lia-agent-system/app/api/v1/*`
- `plataforma-lia/src/components/settings/**`

Failure bloqueia merge. Override só com `[skip-e2e-persistence]` no
commit message + approval explícito.
