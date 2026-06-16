# ADR-029-v2: R4 cross-tenant Header anti-pattern BANIDO + sensor BLOCKING

**Status:** Aprovado 2026-05-20
**Decisor:** Paulo Moraes (via PLANO_ACAO_REPLIT_V3 T-03 + Sprint Execution Protocol)
**Suplementa:** ADR-029 (tool definition unification / multi-tenancy canonical)
**Relaciona:** CLAUDE.md REGRA 6 (R4 enforcement), ADR-LGPD-001

## Contexto

Audit SMOKE-#2 LGPD identificou **28 sites cross-tenant data manipulation** via
`x_company_id: str = Header(..., alias="X-Company-ID")` em handlers FastAPI.

Pattern violava:
- LGPD Art. 6 (finalidade — overwrite JWT permite manipular tenant)
- LGPD Art. 18 (integridade — header não-autenticado decide ownership)
- ADR-029 (multi-tenancy canonical via JWT-derived ContextVar)

Plano V3 T-03 originalmente listou 31 endpoints. Auditoria SSH 2026-05-20:
- Working tree state: trabalho R4 batches 1-3 **já aplicado** em commits anteriores
- Sensor `scripts/check_pydantic_conventions.py` regra R4: **0 violations**
- 14 arquivos `.bak.before-r4-batch{1,2,3}-fix` eram leftover evidence (cleanup)

## Decisão

### Migration aplicada (já em commits anteriores)

22 sites em 15 arquivos migrados de `Header(X-Company-ID)` para `Depends(require_company_id)`:

**Batch 1 — Helpers single-source (mass-effect):**
- admin_agents.py, big_five.py, billing.py (2 sites), client_users.py, communication_settings.py

**Batch 2 — Endpoints diretos:**
- event_history.py, policies.py, rubric_evaluation.py (3 sites), saas_metrics.py, saturation.py (3 sites)

**Batch 3 — Defense-in-depth:**
- technical_tests.py, toon.py (Query OR Header), triagem.py (handler), clients/_shared.py

**Plus 2 sites mantidos canonical:**
- teams.py:408,459 — webhook HMAC-signed (X-Teams-Signature) + `verify_webhook_owner`. Em `SKIP_R4_FUNCTIONS` do sensor. Padrão correto para webhook externo.

### Sensor canonical BLOCKING

Criado `scripts/check_pydantic_R4_only.py` — wrapper isolado que:
- Roda sensor canonical R1+R2+R3+R4
- Parse output, extrai count R4
- Exit 1 se R4 > 0, exit 0 se R4 = 0

**Por que sensor R4 isolado e não promover o geral:**
- Sensor geral (pre-commit hook) é warn-only porque R1=694 e R2=139 ainda têm violations pendentes (T-06/T-07)
- Promover geral para BLOCKING quebraria CI para todo work T-06/T-07 incremental
- Sensor R4 isolado permite BLOCKING enforcement R4 desde já, sem afetar ratchet R1/R2

### Pre-commit + CI integration

Adicionar hook BLOCKING ao `.pre-commit-config.yaml`:

```yaml
- id: pydantic-R4-blocking
  name: "R4 BLOCKING (T-03 ADR-029-v2): no x_company_id via Header"
  language: system
  entry: python3 scripts/check_pydantic_R4_only.py
  files: ^app/.*\.py$
  pass_filenames: false
```

GitHub Actions: adicionar step ao workflow `pydantic-conventions-sensors.yml`.

## Consequências

**Positivas:**
- Multi-tenancy LGPD enforcement reativada (R4 = 0 perpetuamente)
- Drift prevention canonical (qualquer PR novo com `x_company_id Header` falha pre-commit)
- ADR-029 enforcement parcial (R4 done, R1/R2 ratchet seguem T-06/T-07)
- 28 sites cross-tenant LGPD audit SMOKE-#2 fechados

**Negativas:**
- Sensor R4 isolado = pequena duplicação de lógica (wrapper subprocess do sensor canonical)
- Trade-off aceito: BLOCKING granular > BLOCKING all-or-nothing (que atrasaria T-06/T-07)

## Verification

```bash
# Pre-commit local
python scripts/check_pydantic_R4_only.py
# Esperado: exit 0, "OK — 0 violations"

# Sensor canonical full
python scripts/check_pydantic_conventions.py app/
# Esperado: "Pydantic conventions OK" OR R4 line missing
```

## Sensores

| Sensor | Modo | Escopo |
|---|---|---|
| `check_pydantic_R4_only.py` | **BLOCKING** (NEW) | R4 only |
| `check_pydantic_conventions.py` | warn-only | R1+R2+R3+R4 (até T-06/T-07 done) |

## Roadmap follow-up

| Task | Sprint | Escopo |
|---|---|---|
| **T-03 (este)** | 1 | R4 BLOCKING + cleanup .bak |
| T-06 | 2-3 | R2 cleanup (139 → 0) |
| T-07 | 4-6 | R1 ratchet (694 → ratchet sensor) |
| T-14 | 13 | Promover sensor geral pre-commit para BLOCKING (após T-06/T-07 done) |

## Referências

- CLAUDE.md REGRA 6 (R4 enforcement canonical)
- ADR-029 (multi-tenancy canonical original)
- Audit SMOKE-#2 LGPD (28 sites cross-tenant identified)
- PLANO_ACAO_REPLIT_V3_2026-05-20.md T-03
- SPRINT_EXECUTION_PROTOCOL_2026-05-20.md (Protocol Fase A pegou estado real do working tree)
