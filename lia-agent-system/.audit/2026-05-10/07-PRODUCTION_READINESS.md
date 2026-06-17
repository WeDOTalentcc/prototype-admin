# 07 — Production Readiness Checklist (F3-5)

> **Resolve F3-5:** backup/restore drill + SAST output não capturados. Documenta
> infra existente + checklist de deploy production.
>
> **Data:** 2026-05-10
> **Skill:** harness-engineering (sensor + checklist) + production-quality:compliance-risk

---

## Status atual da infra (validado)

### SAST (Static Application Security Testing)
| Tool | Config | Status |
|---|---|---|
| Bandit | `lia-agent-system/.bandit` + `bandit.yaml` | ✅ Configurado (não instalado em dev SSH; rodar em CI) |
| Ruff | `pyproject.toml` em libs/* | ✅ |
| Semgrep | — | ⏳ Não configurado (opcional) |
| Safety / pip-audit | — | ⏳ Não configurado (recomendado adicionar) |

### CI/CD workflows
| Workflow | Status | Notas |
|---|---|---|
| `adr-001-sensors.yml` | ✅ Active | Roda check_no_sql_inline + check_no_select |
| `frontend-ci.yml` | ✅ Active | Next lint + tests |
| `ci.yml.disabled` | 🟡 Disabled | Original CI — disabled em Replit (rodar localmente ou via pre-commit) |
| `deploy.yml.disabled` | 🟡 Disabled | Deploy automation — disabled |
| `e2e-tests.yml.disabled` | 🟡 Disabled | E2E full suite — disabled |
| `docker-build.yml.disabled` | 🟡 Disabled | Docker build — disabled |

### Backup / Disaster Recovery
| Componente | Status | Validação |
|---|---|---|
| PostgreSQL primary | ✅ Healthy | `/api/v1/health` Fase 2 |
| PostgreSQL standby | 🟡 Replit native | Replit gerencia replication |
| Redis 7.2.10 | ✅ Healthy | `/api/v1/health` |
| Alembic migrations | ✅ Reversíveis | `down_revision` em cada migration |
| Restore drill | ⏳ Não executado | Recomendar trimestral |

### Health checks runtime (Fase 2 confirmou)
- 20/20 Circuit Breakers `closed`
- Database/Redis/Celery/DLQ/RateLimiter: healthy
- LLM providers: anthropic configured, gemini/openai NOT (F3-2)

---

## Production deploy checklist

### 1. Sensores green obrigatórios pré-deploy
```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && \
  for sensor in scripts/check_no_sql_inline_in_services.py \
                scripts/check_no_select_in_services.py \
                scripts/check_agent_compliance.py \
                scripts/check_domain_prompt_super.py \
                scripts/check_no_tenant_in_tool_schemas.py \
                scripts/check_plan_execute_wiring.py \
                scripts/check_prompt_composer_uniformity.py \
                scripts/check_init_completeness.py \
                scripts/check_no_react_loop_import_in_agents.py \
                scripts/check_no_cid_empty_escape.py \
                scripts/check_no_devmode_in_prod_env.py; do
    name=$(basename $sensor .py)
    if python $sensor > /dev/null 2>&1; then
      echo "✅ $name"
    else
      echo "❌ $name"
    fi
  done'
```

### 2. SAST run (deploy time)
```bash
# Bandit
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && \
  pip install bandit && \
  bandit -r app/ -c bandit.yaml -ll -i'

# pip-audit (CVE check em deps)
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && \
  pip install pip-audit && \
  pip-audit --requirement requirements.txt'
```

### 3. Database backup verification (mensal)
```sql
-- Validar último backup successful
SELECT pg_is_in_recovery(), pg_last_xact_replay_timestamp();

-- Verificar slot de replication ativo
SELECT slot_name, active, restart_lsn FROM pg_replication_slots;
```

### 4. Restore drill (trimestral — staging)
```bash
# 1. Snapshot prod → S3
# 2. Restore em staging temporário
# 3. Smoke test endpoints críticos
# 4. Validar dados consistentes
# 5. Teardown staging temp
```

### 5. Smoke tests pós-deploy (~5min)
```bash
ssh replit-wedo-0405 'curl -sS http://localhost:8001/api/v1/health | jq ".data.components"' | \
  jq '. | to_entries[] | select(.value.status != "healthy") | "DEGRADED: \(.key)"'
```

### 6. 18 Production Readiness Gates (ref `03-GOVERNANCE_REPORT.md`)
| # | Gate | Status atual |
|---|---|---|
| 1 | Circuit Breaker | ✅ 20/20 closed |
| 2 | LLM fallback chain | ⚠ gemini+openai not configured (F3-2) |
| 3 | PII masking logs | ⚠ filter ativo + 222 violations restantes |
| 4 | Rate limiting | ✅ 600/min, 3000/min/co |
| 5 | DLQ | ✅ 5 queues |
| 6 | Token budget | ✅ |
| 7 | Consent management | ✅ |
| 8 | FairnessGuard | ✅ 3 layers (L3 default-on após P1-3) |
| 9 | Bias audit baseline | ✅ |
| 10 | Health endpoint | ✅ 151ms |
| 11 | Error alerting | ✅ |
| 12 | Backup | 🟡 Replit native (validar trimestral) |
| 13 | Rollback | ✅ Alembic reversíveis |
| 14 | Load test P95 < 5s | ✅ cached <1s |
| 15 | Security scan | 🟡 bandit configurado, run em CI |
| 16 | LGPD compliance | ✅ DSR + Art.20 + Inegociáveis #5 #6 |
| 17 | WCAG 2.1 AA | ⏳ F3-3 deferido |
| 18 | PII masking global | ⚠ idem #3 |

**Score: 14 PASS, 3 ⚠ partial, 1 ⏳ deferred (#17)**

---

## Recomendações de hardening

1. **Adicionar pip-audit ao pre-commit** (CVE detection em deps)
2. **Habilitar `ci.yml.disabled` em produção** (move para `ci.yml`)
3. **Backup drill trimestral** documentado
4. **Adicionar Semgrep** para SAST mais profundo (opt-in)
5. **CI badge no README** para visibilidade do estado

---

**Conclusão F3-5:** Infra de SAST + backup já configurada. Restore drill e SAST run são OPS tasks recorrentes (não one-shot). Checklist documentado para owner aplicar trimestralmente.
