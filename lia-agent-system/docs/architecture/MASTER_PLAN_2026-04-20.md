# PLANO MESTRE — Implementação 100% Pendências LIA

**Aprovado por Paulo** 2026-04-20 | **Baseline auditoria**: MIGRATION-LOG-TOOLS-UNIFIED.md Sessão A

## Executado nesta sessão (Sessão A)

| # | Entrega | Status |
|---|---|---|
| 1 | `scripts/audit_tool_routing.py` criado (CI gate canônico, 4 checks) | ✅ |
| 2 | `docs/architecture/MIGRATION-LOG-TOOLS-UNIFIED.md` gravado | ✅ |
| 3 | Auditoria profunda cruzada (52 checks / 27 tracks, 93% PASS) | ✅ |
| 4 | **Fix `map_intent_to_actionable` regressão** — restaurado em `app/api/v1/chat.py` | ✅ **42/43 testes verdes** |
| 5 | 6 tasks spawnadas para worktrees isolados | ✅ |

## Tasks spawnadas (chips visíveis no cliente — Paulo clica para iniciar em worktree isolado)

| # | Task | Severidade | ETA | Branch proposta |
|---|---|---|---|---|
| 1 | **Admin Tenant Gap — Rails account sync** | 🔴 P0 | ~4h | `feat/admin-tenant-rails-account-sync` |
| 2 | **Onboarding LIA Conversacional — 8 fases** | 🟡 P1 | 2-3 semanas | `feat/onboarding-conversacional-fase-<N>` |
| 3 | **Tool Migration Nível 2 + Nível 3** | 🟡 P1 | 2-3 semanas | `feat/tools-n2-<domain>` / `feat/tools-n3-<group>` |
| 4 | **Kanban 5 bugs + Bias cron + docs sync** | 🟡 P1 | ~4 dias | `fix/kanban-e2e-bugs` / `feat/bias-audit-scheduled` / `docs/production-readiness-sync` |
| 5 | **MIGRATION_PLAN — 18 items restantes** | 🟡 P1 | ~1 semana | `feat/migration-plan-batch-<category>` |
| 6 | **Fix `map_intent_to_actionable`** | — | — | ✅ **FEITO nesta sessão** |

## Sequência recomendada (ordem dependência → impacto)

```
Semana 1:
  Dia 1  ──▶  Admin Tenant Gap (task #1)      [P0 bloqueador]
  Dia 2  ──▶  Kanban + Bias + Docs (task #4)  [UX + compliance rápido]
  Dia 3-5 ─▶  Tool N2 metade 1 (interview_sched, ats_integration, automation, communication)

Semana 2-3:
  Tool N2 metade 2 (cv_screening, analytics, job_management, recruiter_assistant)
  Tool N3 grupos 1-7 (domains menores)

Semana 4-5:
  Tool N3 grupos 8-14 (domains maiores — autonomous 41 tools, pipeline 35, kanban 22)
  MIGRATION_PLAN 18 items (em paralelo)

Semana 6-8:
  Onboarding Conversacional — 8 fases sequenciais
```

## CLAUDE.md non-negotiáveis aplicados em TODO commit

1. **Multi-tenancy**: `company_id` do JWT, nunca do payload
2. **LGPD**: zero dados sensíveis em logs/prompts (raça, religião, gênero, etnia, estado civil, saúde)
3. **Fairness**: rankings/scorings com instrução explícita; audit post-hoc, nunca pré-decisão
4. **No hardcoded secrets**: env vars via `os.environ`
5. **Design tokens**: `00-design-system-v4.2.2.md`, zero cores/spacings hardcoded
6. **Boy Scout rule**: P2s do arquivo no mesmo commit
7. **Review output format**: P0 🔴 / P1 🟡 / P2 🟢

## Skills a rodar após cada task (CLAUDE.md)

```bash
python3 scripts/audit_tool_routing.py           # CI gate canônico
python3 scripts/check_no_pii_in_logs.py         # LGPD
python3 scripts/check_no_sql_in_controllers.py  # ADR-001
python3 scripts/validate_stubs.py
pytest tests/unit/test_action_executor_unit.py  # Regression gate (23 testes)

# Skills manuais por task:
/production-quality                             # review P0/P1/P2
/dei-fairness                                   # se toca ranking/scoring
/lgpd-data-protection                           # se toca dados de candidato
/design:design-critique                         # se toca frontend
```

## Gates automáticos de progresso

### Após Admin Tenant Gap (task #1)
- `pytest tests/integration/test_admin_tenant_rails_sync.py` ✅ 3+ testes
- Smoke: criar cliente Admin → login → dashboard carrega

### Após Tool N2 cada domain
- `audit_tool_routing.py` CHECK 4 cai (baseline 40)
- `pytest tests/unit/test_action_executor_unit.py` 23/23

### Após Tool N3 cada grupo
- `audit_tool_routing.py` CHECK 3 cai (baseline 220)
- `len(tool_registry.list_tools())` cresce proporcionalmente

### Critério final (todas tasks done)
- audit_tool_routing.py: CHECK 1-4 todos PASS (exit 0)
- pytest full suite: 4593+ green (zero regressões)
- MIGRATION_PLAN: 90/90 items done
- PRODUCTION_READINESS_GAPS.md: todos os G-XX RESOLVIDOS ou aceitos

## Convenção de commit / push (Paulo)

- **Nunca `git push`** — Paulo faz manual via Replit IDE na branch replit-sync
- Commits OK no Replit (vão pro histórico local)
- Cada task em branch isolada → rollback independente via `git revert`

## Handoff para cada sessão

Template do prompt inicial (copy-paste):
```
Ler PLANO MESTRE em ~/workspace/lia-agent-system/docs/architecture/MASTER_PLAN_2026-04-20.md
e MIGRATION-LOG em ~/workspace/lia-agent-system/docs/architecture/MIGRATION-LOG-TOOLS-UNIFIED.md.

Executar: [nome da task — ex: "Tool Migration N2 — interview_scheduling domain"]

SSH: ssh -i ~/.ssh/replit -p 22 82791557-0b63-4f8d-baed-bba54c6e1fdf@82791557-0b63-4f8d-baed-bba54c6e1fdf-00-32kinhguzv9ak.picard.replit.dev
Aplicar CLAUDE.md em cada commit.
Paulo commita manual via Replit IDE.
Reportar progresso em MIGRATION-LOG ao fim.
```

---

## Métricas de sucesso

| Dimensão | Baseline (Sessão A) | Target final |
|---|---|---|
| Auditoria cruzada tracks | 93% PASS (25/27) | **100% PASS** |
| CHECK 1 (intents órfãos) | 1 WARN | PASS |
| CHECK 3 (V2 ToolDefs fora registry) | 220 | **0** |
| CHECK 4 (V1 handlers broken) | 40/94 | **0** |
| Testes unit | 4593 (1 err collection) | 4593+ green, zero err |
| Testes map_intent | 42/43 passed | 43/43 |
| MIGRATION_PLAN items | 72/90 | 90/90 |
| PRODUCTION_READINESS gaps abertos | ~6 | 0 |
| Onboarding Conversacional fases | 0/8 | 8/8 |
| Kanban E2E | 42/50 | 50/50 |

## Observações estratégicas

**Pontos fortes descobertos**:
- Stub ratio de 0,5% (excelente — código real, não mocks)
- 473k LOC com 4593 testes (densidade alta)
- Bandit + pip-audit JÁ no CI (PRODUCTION_READINESS_GAPS.md estava desatualizado)
- Golden datasets JÁ existem
- 62 domains estruturados + 14 ReAct agents maduros

**Riscos monitorados**:
- 861 commits ahead of origin/main (branch drift — replit-sync workflow OK mas monitorar conflitos)
- Tool Migration N3 top-3 arquivos (autonomous 41, pipeline 35, kanban 22) são cross-cutting — testes de regressão importantes
- Onboarding Conversacional toca UX crítica — design review por fase mandatório

**Para revisar em 2 semanas**:
- Reavaliar ETAs conforme velocidade real das primeiras sessões
- Ajustar sequência se aparecerem dependências não previstas
- Considerar spawnar Onboarding fases 5-8 apenas após fases 1-4 validadas em prod
